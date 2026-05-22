from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from tracewise.analysis.triage import analyze_incident
from tracewise.core.models import IncidentBundle, TriageReport

app = FastAPI(title="TraceWise", version="0.1.0")


class TriageRequest(BaseModel):
    incident: IncidentBundle
    query: str = "What is the most likely root cause?"
    retriever: str = "keyword"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageReport)
def triage(request: TriageRequest) -> TriageReport:
    return analyze_incident(request.incident, query=request.query, retriever_mode=request.retriever)
