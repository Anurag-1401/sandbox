from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any,Protocol

from transformers import AutoTokenizer


class TokenizerProtocol(Protocol):
    model_max_length: int

    def encode(
        self,
        text: str,
        add_special_tokens: bool = False,
    ) -> list[int]:
        ...

    def decode(
        self,
        token_ids: list[int],
        skip_special_tokens: bool = True,
    ) -> str:
        ...

@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    token_count: int
    page_start: int
    page_end: int


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 220,
        overlap: int = 40,
        tokenizer: TokenizerProtocol | None = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.tokenizer = tokenizer or self._load_tokenizer(model_name)

        model_limit = self.tokenizer.model_max_length

        # Leave room for special tokens added by the embedding model.
        if model_limit > 0 and model_limit < 100_000:
            safe_limit = model_limit - 2
            if chunk_size > safe_limit:
                raise ValueError(
                    f"chunk_size={chunk_size} exceeds the safe tokenizer "
                    f"limit of {safe_limit}"
                )

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.stride = chunk_size - overlap

    @staticmethod
    def _load_tokenizer(model_name: str) -> TokenizerProtocol:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Install transformers to use the production tokenizer"
            ) from exc

        return AutoTokenizer.from_pretrained(model_name)

    def chunk_text(
        self,
        text: str,
        page_number: int = 1,
    ) -> list[TextChunk]:
        if not text or not text.strip():
            return []

        token_ids = self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        if not token_ids:
            return []

        chunks: list[TextChunk] = []

        for start in range(0, len(token_ids), self.stride):
            end = min(start + self.chunk_size, len(token_ids))
            chunk_tokens = token_ids[start:end]

            content = self.tokenizer.decode(
                chunk_tokens,
                skip_special_tokens=True,
            ).strip()

            if content:
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        content=content,
                        token_count=len(chunk_tokens),
                        page_start=page_number,
                        page_end=page_number,
                    )
                )

            if end == len(token_ids):
                break

        return chunks

    def chunk_pages(
        self,
        pages: list[dict[str, Any]],
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []

        for page in pages:
            page_number = int(page["page_number"])
            text = page.get("text", "")

            page_chunks = self.chunk_text(
                text=text,
                page_number=page_number,
            )

            for chunk in page_chunks:
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        content=chunk.content,
                        token_count=chunk.token_count,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                    )
                )

        return chunks