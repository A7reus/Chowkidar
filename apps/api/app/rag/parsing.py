from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_pdf_with_pypdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def parse_with_docling(path: Path) -> str:
    from docling.document_converter import DocumentConverter  # pyright: ignore[reportMissingImports]

    result = DocumentConverter().convert(str(path))
    return result.document.export_to_markdown()


def parse_document(filename: str, data: bytes, tmp_dir: Path | None = None) -> tuple[str, str]:
    """Return (text, parser_name). Docling is preferred for office/PDF files."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json"}:
        return parse_text(data), "plain-text"
    if suffix == ".pdf":
        try:
            if tmp_dir is not None:
                tmp_dir.mkdir(parents=True, exist_ok=True)
                path = tmp_dir / filename
                path.write_bytes(data)
                return parse_with_docling(path), "docling"
        except Exception as exc:
            logger.info("Docling parsing failed; falling back to pypdf: %s", exc)
        try:
            return parse_pdf_with_pypdf(data), "pypdf"
        except Exception as exc:
            raise ValueError(f"Unable to parse PDF: {exc}") from exc
    if suffix in {".docx", ".pptx", ".xlsx", ".html"} and tmp_dir is not None:
        try:
            tmp_dir.mkdir(parents=True, exist_ok=True)
            path = tmp_dir / filename
            path.write_bytes(data)
            return parse_with_docling(path), "docling"
        except Exception as exc:
            raise ValueError(f"Unable to parse {suffix}: {exc}") from exc
    raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")
