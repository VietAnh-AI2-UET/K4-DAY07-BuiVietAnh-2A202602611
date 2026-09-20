from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
            
        # Tách câu dựa trên dấu chấm, chấm than, hỏi chấm kèm khoảng trắng hoặc xuống dòng
        # Sử dụng lookbehind (?<=...) để giữ lại dấu câu ở cuối mỗi câu
        sentences = re.split(r'(?<=\.) |(?<=\!) |(?<=\?) |(?<=\.)\n', text)
        
        # Loại bỏ các chuỗi rỗng và khoảng trắng thừa
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            chunks.append(chunk.strip())
            
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
            
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        if not remaining_separators:
            return [current_text]
            
        separator = remaining_separators[0]
        new_separators = remaining_separators[1:]
        
        # Nếu separator là chuỗi rỗng, tách thành từng ký tự để tránh ValueError
        if separator == "":
            splits = list(current_text)
        else:
            splits = current_text.split(separator)
            
        chunks = []
        current_chunk = []
        current_len = 0
        
        for s in splits:
            if len(s) <= self.chunk_size:
                # Tính độ dài nếu thêm s vào current_chunk
                sep_len = len(separator) if current_chunk else 0
                if current_len + sep_len + len(s) > self.chunk_size and current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                    sep_len = 0
                    
                current_chunk.append(s)
                current_len += sep_len + len(s)
            else:
                # Nếu s quá dài, đẩy current_chunk hiện tại vào kết quả
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                    
                # Đệ quy cắt nhỏ s
                sub_chunks = self._split(s, new_separators)
                chunks.extend(sub_chunks)
                
        # Đẩy nốt phần còn dư
        if current_chunk:
            chunks.append(separator.join(current_chunk))
            
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_prod = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_prod / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size).chunk(text)
        sentence = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        
        def _stats(chunks: list[str]) -> dict:
            return {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0.0,
                "chunks": chunks
            }
            
        return {
            "fixed_size": _stats(fixed),
            "by_sentences": _stats(sentence),
            "recursive": _stats(recursive)
        }
