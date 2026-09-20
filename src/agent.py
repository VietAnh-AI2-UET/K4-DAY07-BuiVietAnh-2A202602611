from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Cơ sở dữ liệu hiện đang trống. Vui lòng thêm tài liệu trước khi tìm kiếm."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."

        context_parts = []
        for idx, r in enumerate(results, start=1):
            source = r.get("metadata", {}).get("doc_id", "Unknown")
            context_parts.append(f"[{idx}] (Nguồn: {source})\n{r['content']}")
        
        context_str = "\n\n".join(context_parts)
        prompt = (
            "Bạn là một trợ lý ảo trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.\n"
            "Tuyệt đối tuân thủ các quy tắc sau:\n"
            "1. Chỉ sử dụng thông tin từ ngữ cảnh bên dưới để trả lời.\n"
            "2. Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy nói rõ \"Tôi không tìm thấy thông tin phù hợp.\"\n"
            "3. Bắt buộc trích dẫn nguồn bằng số thứ tự của đoạn ngữ cảnh (ví dụ: [1], [2]) trong câu trả lời.\n\n"
            "Ngữ cảnh:\n"
            f"{context_str}\n\n"
            "Câu hỏi:\n"
            f"{question}\n\n"
            "Câu trả lời:"
        )
        return self.llm_fn(prompt)
