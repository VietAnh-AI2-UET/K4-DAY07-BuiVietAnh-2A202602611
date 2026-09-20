import sys
from pathlib import Path

from src.chunking import ChunkingStrategyComparator

def extract_frontmatter(content: str) -> tuple[dict, str]:
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    metadata[k] = v
    return metadata, body

def main():
    docs = [
        "data/ecommerce/buyer-return-refund-policy.md",
        "data/ecommerce/seller-return-refund-response.md"
    ]
    
    comparator = ChunkingStrategyComparator()
    
    for doc_path in docs:
        path = Path(doc_path)
        if not path.exists():
            print(f"File not found: {path}")
            continue
            
        raw_text = path.read_text(encoding="utf-8")
        _, body = extract_frontmatter(raw_text)
        
        print(f"\n=== Document: {path.name} ===")
        results = comparator.compare(body, chunk_size=500)
        
        for strategy_name, stats in results.items():
            print(f"Strategy: {strategy_name}")
            print(f"  Count: {stats['count']}")
            print(f"  Avg Length: {stats['avg_length']:.2f}")

if __name__ == "__main__":
    main()
