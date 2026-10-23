from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.rag.embeddings import get_embedding_service


@dataclass
class Chunk:
    content: str
    citation_label: str
    citation_url: str
    section_path: str
    metadata: dict[str, Any]
    embedding: list[float]


def split_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return []
    try:
        from llama_index.core.node_parser import SentenceSplitter

        splitter = SentenceSplitter(chunk_size=max_chars, chunk_overlap=overlap)
        return [chunk.strip() for chunk in splitter.split_text(cleaned) if chunk.strip()]
    except Exception:
        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(start + max_chars, len(cleaned))
            chunks.append(cleaned[start:end].strip())
            start = max(end - overlap, end)
        return [chunk for chunk in chunks if chunk]


def build_signal_chunks(
    *,
    title: str,
    raw_text: str,
    jurisdiction: str,
    citation_url: str,
    citation_label: str,
    section_path: str = "Body",
    extra: dict[str, Any] | None = None,
) -> list[Chunk]:
    service = get_embedding_service()
    pieces = split_text(raw_text)
    if not pieces:
        pieces = [title]
    contextual = [
        f"Document: {title}\nJurisdiction: {jurisdiction}\nSection: {section_path}\n\n{piece}"
        for piece in pieces
    ]
    embeddings = service.embed_texts(contextual)
    return [
        Chunk(
            content=contextual[index],
            citation_label=citation_label,
            citation_url=citation_url,
            section_path=section_path,
            metadata={"title": title, "jurisdiction": jurisdiction, **(extra or {})},
            embedding=embeddings[index],
        )
        for index, piece in enumerate(pieces)
    ]
