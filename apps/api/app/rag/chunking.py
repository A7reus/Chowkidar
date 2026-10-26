from __future__ import annotations

import re
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


HEADING_RE = re.compile(
    r"^(?:(?:article|section|chapter|part|annex|schedule|rule|title)\s+[0-9ivxlcdm]+[a-z]?\b"
    r"|§\s*\d+)",
    re.IGNORECASE,
)
MAX_HEADING_CHARS = 120


def is_heading(line: str) -> bool:
    """Recognise legal-structure headings such as ``Article 5 — Due diligence``."""
    stripped = line.strip()
    return (
        bool(HEADING_RE.match(stripped))
        and len(stripped) <= MAX_HEADING_CHARS
        and not stripped.endswith((".", ";", ","))
    )


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split text at legal headings so chunks never straddle two articles.

    Returns ``(heading, body)`` pairs. Text before the first heading gets an
    empty heading. Sections vary in size with the source structure; long ones
    are sentence-split afterwards by :func:`split_text`.
    """
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        if is_heading(line):
            sections.append((line.strip(), []))
        else:
            sections[-1][1].append(line)
    result: list[tuple[str, str]] = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if body or heading:
            result.append((heading, body))
    return result


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
    pieces: list[tuple[str, str]] = []
    for heading, body in split_sections(raw_text):
        path = f"{section_path} › {heading}" if heading else section_path
        for piece in split_text(body) or ([heading] if heading else []):
            pieces.append((path, piece))
    if not pieces:
        pieces = [(section_path, title)]
    contextual = [
        f"Document: {title}\nJurisdiction: {jurisdiction}\nSection: {path}\n\n{piece}"
        for path, piece in pieces
    ]
    embeddings = service.embed_texts(contextual)
    return [
        Chunk(
            content=contextual[index],
            citation_label=citation_label,
            citation_url=citation_url,
            section_path=path,
            metadata={
                "title": title,
                "jurisdiction": jurisdiction,
                "chunking": "structure-aware",
                **(extra or {}),
            },
            embedding=embeddings[index],
        )
        for index, (path, _piece) in enumerate(pieces)
    ]
