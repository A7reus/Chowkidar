from __future__ import annotations

from app.rag.chunking import build_signal_chunks, is_heading, split_sections

DIRECTIVE = """Directive (EU) 2024/1760 on corporate sustainability due diligence.

Article 5 — Due diligence

1. Member States shall ensure that companies conduct risk-based due diligence
as laid down in Articles 7 to 16.

Article 8 — Identifying actual and potential adverse impacts

1. Companies shall take appropriate measures to identify adverse impacts."""


def test_headings_are_legal_structure_lines_not_sentences() -> None:
    assert is_heading("Article 5 — Due diligence")
    assert is_heading("Section 12(b)")
    assert is_heading("§ 4 Reporting duties")
    assert not is_heading("Article 7 requires companies to integrate due diligence.")
    assert not is_heading("Article 7 requires companies to integrate due diligence")
    assert not is_heading("as laid down in Articles 7 to 16.")
    assert not is_heading("Articles of association were filed")


def test_split_sections_keeps_each_article_separate() -> None:
    sections = split_sections(DIRECTIVE)
    assert [heading for heading, _ in sections] == [
        "",
        "Article 5 — Due diligence",
        "Article 8 — Identifying actual and potential adverse impacts",
    ]
    assert "Articles 7 to 16" in sections[1][1]
    assert "identify adverse impacts" in sections[2][1]


def test_chunks_carry_article_level_section_paths_and_context() -> None:
    chunks = build_signal_chunks(
        title="EU CSDDD",
        raw_text=DIRECTIVE,
        jurisdiction="EU",
        citation_url="https://eur-lex.europa.eu/eli/dir/2024/1760/oj",
        citation_label="EUR-Lex — CSDDD",
        section_path="Signal body",
    )
    paths = [chunk.section_path for chunk in chunks]
    assert "Signal body › Article 5 — Due diligence" in paths
    article_8 = next(chunk for chunk in chunks if chunk.section_path.endswith("adverse impacts"))
    assert article_8.content.startswith("Document: EU CSDDD\nJurisdiction: EU\nSection: Signal body ›")
    assert "Articles 7 to 16" not in article_8.content
    assert all(chunk.metadata["chunking"] == "structure-aware" for chunk in chunks)


def test_text_without_headings_still_produces_one_section() -> None:
    chunks = build_signal_chunks(
        title="Port strike",
        raw_text="Port workers announced a 48-hour strike.",
        jurisdiction="BD",
        citation_url="https://example.org/news",
        citation_label="GDELT — Port strike",
    )
    assert [chunk.section_path for chunk in chunks] == ["Body"]
