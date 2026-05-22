from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    LOG = "log"
    STACK_TRACE = "stack_trace"
    CODE = "code"
    CONFIG = "config"
    TEST_OUTPUT = "test_output"
    NOTE = "note"


class IncidentArtifact(BaseModel):
    artifact_id: str
    artifact_type: ArtifactType
    path: str
    text: str


class IncidentBundle(BaseModel):
    incident_id: str
    title: str
    summary: str = ""
    artifacts: list[IncidentArtifact] = Field(default_factory=list)


class EvidenceChunk(BaseModel):
    chunk_id: str
    incident_id: str
    artifact_id: str
    artifact_type: ArtifactType
    path: str
    text: str
    start_line: int
    end_line: int

    @property
    def citation(self) -> str:
        return f"{self.path}:{self.start_line}-{self.end_line}"


class RetrievalHit(BaseModel):
    chunk: EvidenceChunk
    score: float
    matched_terms: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    timestamp: str
    source: str
    message: str
    citation: str


class RootCauseHypothesis(BaseModel):
    label: str
    confidence: float
    rationale: str
    citations: list[str]


class TriageReport(BaseModel):
    incident_id: str
    title: str
    executive_summary: str
    hypotheses: list[RootCauseHypothesis]
    timeline: list[TimelineEvent]
    evidence: list[RetrievalHit]
    recommended_fix_plan: list[str]


class EvaluationCase(BaseModel):
    incident_dir: Path
    expected_cause_keywords: list[str]
    query: str = "What is the most likely root cause?"
