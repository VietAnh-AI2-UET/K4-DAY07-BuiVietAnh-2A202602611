import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.models import Document
from src.store import EmbeddingStore
from src.chunking import RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

# 5 benchmark queries đã chốt của nhóm
QUERIES = [
    {
        "text": "Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn giao thành công? Riêng thực phẩm tươi sống/đông lạnh thì sao?",
        "filter": None,
        "gold_doc": "buyer-return-refund-policy"
    },
    {
        "text": "Khi không đồng ý với quyết định hoàn tiền của Shopee, người bán phải phản hồi trong bao lâu?",
        "filter": {"audience": "seller"},
        "gold_doc": "seller-return-refund-response"
    },
    {
        "text": "Người mua có thể yêu cầu trả hàng/hoàn tiền trong những trường hợp nào?",
        "filter": None,
        "gold_doc": "buyer-return-refund-policy"
    },
    {
        "text": "Người bán vi phạm chính sách chống gian lận có thể phải bồi thường tối đa bao nhiêu cho mỗi đơn hàng vi phạm?",
        "filter": None,
        "gold_doc": "shopee-chinh-sach-chong-gian-lan-nguoi-ban"
    },
    {
        "text": "Nếu Shopee Mall phát hiện người bán bán hàng giả, hàng nhái, hàng không rõ xuất xứ hoặc phân phối bất hợp pháp, mức phí và thời hạn thanh toán là gì?",
        "filter": None,
        "gold_doc": "dieu-khoan-shopee-mall"
    }
]

def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Basic extraction of YAML frontmatter."""
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            # Parse đơn giản các dòng key: value
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    metadata[k] = v
    return metadata, body

def main():
    print("=== Khởi tạo Benchmark CP5 ===")
    data_dir = Path("data/ecommerce")
    md_files = list(data_dir.glob("*.md"))
    
    if not md_files:
        print(f"Không tìm thấy file .md nào trong {data_dir}")
        return

    # --- DÒNG CHỌN CHUNKER (Mỗi người sửa dòng này theo nhiệm vụ của mình) ---
    chunker = FixedSizeChunker(chunk_size=500)
    # -------------------------------------------------------------------------

    docs_to_store = []
    
    # 1. Đọc file, tách frontmatter và phần thân
    # 2. Chunk phần thân, trải metadata vào mỗi chunk
    print("Đang đọc và chunk tài liệu...")
    for file_path in md_files:
        raw_text = file_path.read_text(encoding="utf-8")
        metadata, body = extract_frontmatter(raw_text)
        
        # Bổ sung doc_id vào metadata từ tên file
        metadata["doc_id"] = file_path.stem
        
        chunks = chunker.chunk(body)
        for i, chunk_text in enumerate(chunks):
            doc = Document(
                id=f"{file_path.stem}#{i}",
                content=chunk_text,
                metadata=metadata.copy()  # Trải metadata vào mọi chunk
            )
            docs_to_store.append(doc)
            
    print(f"Đã tạo {len(docs_to_store)} chunks từ {len(md_files)} files.")

    # Tải biến môi trường (.env) để lấy API key
    load_dotenv(override=False)
    
    # Lấy Embedder (giống như trong main.py)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    elif provider == "gemini":
        try:
            embedder = GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    print(f"Sử dụng Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    # 3. Nạp vào EmbeddingStore
    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=embedder)
    store.add_documents(docs_to_store)
    print(f"Đã nạp {store.get_collection_size()} chunks vào EmbeddingStore.\n")

    # 4. Chạy 5 query và in top 3
    print("=== BẮT ĐẦU CHẠY BENCHMARK 5 CÂU HỎI ===")
    
    for idx, q in enumerate(QUERIES, 1):
        print(f"\n[Câu {idx}] {q['text']}")
        if q['filter']:
            print(f"  -> Lọc với metadata: {q['filter']}")
            
        # Gọi hàm search_with_filter
        results = store.search_with_filter(
            query=q['text'],
            top_k=3,
            metadata_filter=q['filter']
        )
        
        # In ra top 3 kết quả
        for rank, res in enumerate(results, 1):
            doc_id = res['metadata'].get('doc_id', 'unknown')
            score = res['score']
            
            # Gắn icon check nếu kết quả tìm thấy khớp với gold answer
            is_gold = "✅" if q['gold_doc'] in doc_id else "❌"
            
            preview = res['content'].replace("\n", " ")[:100]
            print(f"  Top {rank} {is_gold} | Score: {score:.4f} | Doc: {doc_id}")
            print(f"         Nội dung: {preview}...")

if __name__ == "__main__":
    main()
