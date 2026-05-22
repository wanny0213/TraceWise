from __future__ import annotations

import re
from collections import defaultdict

from tracewise.core.models import (
    IncidentBundle,
    RetrievalHit,
    RootCauseHypothesis,
    TimelineEvent,
    TriageReport,
)
from tracewise.ingestion.chunking import chunk_bundle
from tracewise.retrieval.factory import Retriever, build_retriever

TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z)?\b")

SIGNALS = {
    "configuration regression": [
        "missing environment variable",
        "env var",
        "configuration",
        "config",
        "secret",
        "api key",
    ],
    "api contract mismatch": [
        "unexpected field",
        "schema",
        "contract",
        "validation",
        "deserialize",
        "jsondecode",
    ],
    "dependency or version regression": [
        "version",
        "dependency",
        "upgrade",
        "package",
        "incompatible",
    ],
    "timeout or upstream outage": [
        "timeout",
        "timed out",
        "503",
        "504",
        "connection refused",
        "upstream",
    ],
    "test failure regression": [
        "assertionerror",
        "failed",
        "pytest",
        "expected",
        "actual",
    ],
}


def analyze_incident(
    bundle: IncidentBundle,
    query: str = "What is the most likely root cause?",
    retriever_mode: str = "keyword",
) -> TriageReport:
    chunks = chunk_bundle(bundle.incident_id, bundle.artifacts)
    retriever = build_retriever(chunks, mode=retriever_mode)
    query_hits = retriever.search(query, top_k=8)
    signal_hits = _collect_signal_hits(retriever)
    evidence = _merge_hits(query_hits + signal_hits)
    hypotheses = _rank_hypotheses(evidence)
    timeline = _extract_timeline(evidence)
    summary = _build_summary(bundle, hypotheses)

    return TriageReport(
        incident_id=bundle.incident_id,
        title=bundle.title,
        executive_summary=summary,
        hypotheses=hypotheses,
        timeline=timeline,
        evidence=evidence,
        recommended_fix_plan=_fix_plan(hypotheses),
    )


def _collect_signal_hits(retriever: Retriever) -> list[RetrievalHit]:
    hits: list[RetrievalHit] = []
    for terms in SIGNALS.values():
        hits.extend(retriever.search(" ".join(terms), top_k=3))
    return hits


def _merge_hits(hits: list[RetrievalHit]) -> list[RetrievalHit]:
    by_chunk: dict[str, RetrievalHit] = {}
    for hit in hits:
        existing = by_chunk.get(hit.chunk.chunk_id)
        if existing is None or hit.score > existing.score:
            by_chunk[hit.chunk.chunk_id] = hit
    return sorted(by_chunk.values(), key=lambda hit: hit.score, reverse=True)[:10]


def _rank_hypotheses(evidence: list[RetrievalHit]) -> list[RootCauseHypothesis]:
    scores: defaultdict[str, float] = defaultdict(float)
    citations: defaultdict[str, list[str]] = defaultdict(list)
    text_by_label: defaultdict[str, list[str]] = defaultdict(list)

    for hit in evidence:
        text = hit.chunk.text.lower()
        for label, terms in SIGNALS.items():
            matches = [term for term in terms if term in text]
            if not matches:
                continue
            scores[label] += hit.score + len(matches)
            citations[label].append(hit.chunk.citation)
            text_by_label[label].append(hit.chunk.text)

    if not scores and evidence:
        top = evidence[0]
        return [
            RootCauseHypothesis(
                label="insufficient evidence for a specific root cause",
                confidence=0.35,
                rationale="The available artifacts contain relevant incident evidence, but no known triage signal is strong enough to name a specific cause.",
                citations=[top.chunk.citation],
            )
        ]

    total = sum(scores.values()) or 1.0
    hypotheses = []
    for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]:
        confidence = min(0.95, max(0.4, score / total))
        hypotheses.append(
            RootCauseHypothesis(
                label=label,
                confidence=round(confidence, 2),
                rationale=_rationale(label, text_by_label[label]),
                citations=sorted(set(citations[label]))[:4],
            )
        )
    return hypotheses


def _rationale(label: str, snippets: list[str]) -> str:
    sample = " ".join(snippets).lower()
    if label == "configuration regression":
        return "Evidence mentions missing configuration, secrets, or environment variables near the failure path."
    if label == "api contract mismatch":
        return "Evidence points to schema, validation, or serialization errors after the request reached application code."
    if label == "dependency or version regression":
        return "Evidence references dependency/version changes that can explain a new behavioral regression."
    if label == "timeout or upstream outage":
        return "Evidence contains timeout or upstream availability failures during the incident window."
    if "assertionerror" in sample or "pytest" in sample:
        return "Failing tests reproduce the incident behavior and narrow the regression surface."
    return "Evidence matches a known incident signal across the uploaded artifacts."


def _extract_timeline(evidence: list[RetrievalHit]) -> list[TimelineEvent]:
    events = []
    for hit in evidence:
        for line_number, line in enumerate(hit.chunk.text.splitlines(), start=hit.chunk.start_line):
            timestamp = TIMESTAMP_RE.search(line)
            if not timestamp:
                continue
            events.append(
                TimelineEvent(
                    timestamp=timestamp.group(0),
                    source=hit.chunk.path,
                    message=line.strip(),
                    citation=f"{hit.chunk.path}:{line_number}",
                )
            )
    return sorted(events, key=lambda event: event.timestamp)[:12]


def _build_summary(bundle: IncidentBundle, hypotheses: list[RootCauseHypothesis]) -> str:
    if not hypotheses:
        return f"TraceWise found incident evidence for {bundle.title}, but no root-cause hypothesis met the evidence threshold."
    top = hypotheses[0]
    return f"TraceWise ranks '{top.label}' as the leading cause for {bundle.title} with {top.confidence:.0%} confidence based on cited artifacts."


def _fix_plan(hypotheses: list[RootCauseHypothesis]) -> list[str]:
    if not hypotheses:
        return ["Collect more logs, stack traces, and reproduction output before changing code."]

    top = hypotheses[0].label
    if top == "configuration regression":
        return [
            "Compare runtime configuration against the last healthy deployment.",
            "Add startup validation for required environment variables and secrets.",
            "Add a regression test that fails when required configuration is absent.",
        ]
    if top == "api contract mismatch":
        return [
            "Inspect producer and consumer schemas for the failing request path.",
            "Add compatibility handling for the unexpected or missing field.",
            "Pin the failing payload as a contract regression test.",
        ]
    if top == "timeout or upstream outage":
        return [
            "Check upstream health, timeout budgets, and retry behavior during the incident window.",
            "Add fallback or circuit-breaker behavior for repeated upstream failures.",
            "Create an alert for elevated timeout rates before user-facing failure.",
        ]
    return [
        "Reproduce the issue with the cited failing path.",
        "Patch the smallest suspected component.",
        "Add a regression test tied to the cited evidence.",
    ]
