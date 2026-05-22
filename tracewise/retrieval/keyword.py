from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from tracewise.core.models import EvidenceChunk, RetrievalHit

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_./:-]{1,}")
STOPWORDS = {
    "the",
    "and",
    "for",
    "from",
    "with",
    "that",
    "this",
    "what",
    "most",
    "likely",
    "root",
    "cause",
    "incident",
}


class KeywordRetriever:
    def __init__(self, chunks: list[EvidenceChunk]):
        self.chunks = chunks
        self._term_freqs = [_token_counts(chunk.text) for chunk in chunks]
        document_frequency: defaultdict[str, int] = defaultdict(int)
        for counts in self._term_freqs:
            for term in counts:
                document_frequency[term] += 1
        self._document_frequency = dict(document_frequency)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        query_terms = [term for term in _tokens(query) if term not in STOPWORDS]
        if not query_terms:
            query_terms = [term for term in _tokens(query)]

        hits = []
        for chunk, counts in zip(self.chunks, self._term_freqs):
            score = 0.0
            matched_terms = []
            for term in query_terms:
                if term not in counts:
                    continue
                idf = math.log((1 + len(self.chunks)) / (1 + self._document_frequency[term])) + 1
                score += counts[term] * idf
                matched_terms.append(term)
            if score > 0:
                hits.append(RetrievalHit(chunk=chunk, score=round(score, 4), matched_terms=matched_terms))

        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]


def _token_counts(text: str) -> Counter[str]:
    return Counter(_tokens(text))


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
