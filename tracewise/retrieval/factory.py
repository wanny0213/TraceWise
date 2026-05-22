from __future__ import annotations

from typing import Protocol

from tracewise.core.models import EvidenceChunk, RetrievalHit
from tracewise.retrieval.keyword import KeywordRetriever
from tracewise.retrieval.vector import LocalVectorRetriever

RetrieverMode = str


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        ...


def build_retriever(chunks: list[EvidenceChunk], mode: RetrieverMode = "keyword") -> Retriever:
    if mode == "keyword":
        return KeywordRetriever(chunks)
    if mode == "vector":
        return LocalVectorRetriever(chunks)
    raise ValueError(f"Unsupported retriever mode: {mode}")
