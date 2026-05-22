from __future__ import annotations

import math
from collections import Counter, defaultdict

from tracewise.core.models import EvidenceChunk, RetrievalHit
from tracewise.retrieval.keyword import STOPWORDS, _tokens


class LocalVectorRetriever:
    """Dependency-free TF-IDF cosine retriever.

    This is intentionally lightweight: it gives TraceWise a vector-style
    baseline that is deterministic in tests and easy to compare with keyword
    retrieval before adding external embedding models.
    """

    def __init__(self, chunks: list[EvidenceChunk]):
        self.chunks = chunks
        self._term_freqs = [_token_counts(chunk.text) for chunk in chunks]
        document_frequency: defaultdict[str, int] = defaultdict(int)
        for counts in self._term_freqs:
            for term in counts:
                document_frequency[term] += 1
        self._idf = {
            term: math.log((1 + len(chunks)) / (1 + frequency)) + 1
            for term, frequency in document_frequency.items()
        }
        self._vectors = [_tf_idf_vector(counts, self._idf) for counts in self._term_freqs]
        self._norms = [_norm(vector) for vector in self._vectors]

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        query_terms = [term for term in _tokens(query) if term not in STOPWORDS]
        if not query_terms:
            query_terms = _tokens(query)

        query_counts = Counter(query_terms)
        query_vector = _tf_idf_vector(query_counts, self._idf)
        query_norm = _norm(query_vector)
        if query_norm == 0:
            return []

        hits = []
        for chunk, vector, norm in zip(self.chunks, self._vectors, self._norms):
            if norm == 0:
                continue
            score = _dot(query_vector, vector) / (query_norm * norm)
            if score <= 0:
                continue
            matched_terms = sorted(set(query_vector).intersection(vector))
            hits.append(RetrievalHit(chunk=chunk, score=round(score, 4), matched_terms=matched_terms))

        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]


def _token_counts(text: str) -> Counter[str]:
    return Counter(term for term in _tokens(text) if term not in STOPWORDS)


def _tf_idf_vector(counts: Counter[str], idf: dict[str, float]) -> dict[str, float]:
    vector = {}
    for term, count in counts.items():
        if term in idf:
            vector[term] = count * idf[term]
    return vector


def _dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())


def _norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))
