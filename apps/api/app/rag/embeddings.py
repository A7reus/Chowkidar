from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence

from app.core.config import get_settings

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def mock_embedding(text: str, dim: int = 1024) -> list[float]:
    """Deterministic hash embedding for offline mode.

    It is not semantically meaningful, but it keeps the pgvector path,
    dimensions, and API contract identical to live mode.
    """
    vector = [0.0] * dim
    tokens = TOKEN_RE.findall(text.lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def lexical_overlap(query: str, document: str) -> float:
    query_tokens = set(TOKEN_RE.findall(query.lower()))
    doc_tokens = set(TOKEN_RE.findall(document.lower()))
    if not query_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


class EmbeddingService:
    """Lazy wrapper around FlagEmbedding with a deterministic fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._reranker = None
        self._live_ready = False
        self._load_attempted = False

    def _load(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True
        if self.settings.embedding_mode != "live":
            return
        try:
            from FlagEmbedding import BGEM3FlagModel, FlagReranker  # type: ignore[import-not-found]

            self._model = BGEM3FlagModel(self.settings.embedding_model, use_fp16=False)
            self._reranker = FlagReranker(self.settings.reranker_model, use_fp16=False)
            self._live_ready = True
        except Exception:
            self._live_ready = False

    @property
    def live_ready(self) -> bool:
        self._load()
        return self._live_ready

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._load()
        if self._live_ready and self._model is not None:
            output = self._model.encode(
                texts,
                batch_size=8,
                max_length=1024,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            dense = output["dense_vecs"]
            return [list(map(float, vector)) for vector in dense]
        return [mock_embedding(text, self.settings.embedding_dim) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        self._load()
        if self._live_ready and self._reranker is not None and documents:
            pairs = [[query, document] for document in documents]
            scores = self._reranker.compute_score(pairs, normalize=True)
            if isinstance(scores, float):
                scores = [scores]
            ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
            return [(index, float(score)) for index, score in ranked[:top_k]]
        ranked = [
            (index, lexical_overlap(query, document))
            for index, document in enumerate(documents)
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:top_k]


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
