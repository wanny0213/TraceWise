from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

import streamlit as st

from tracewise.analysis.triage import analyze_incident
from tracewise.ingestion.bundles import load_incident_bundle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INCIDENTS_DIR = PROJECT_ROOT / "incidents"
EVAL_CASES_PATH = PROJECT_ROOT / "eval_cases.json"


def main() -> None:
    st.set_page_config(page_title="TraceWise", page_icon="TW", layout="wide")
    _inject_styles()

    incident_dirs = sorted(
        path for path in INCIDENTS_DIR.iterdir() if path.is_dir() and (path / "incident.json").exists()
    )
    if not incident_dirs:
        st.error("No incident bundles found.")
        return

    with st.sidebar:
        st.markdown("## TraceWise")
        st.caption("Evidence-grounded incident triage")
        selected = st.selectbox("Incident bundle", incident_dirs, format_func=lambda path: path.name)
        query = st.text_area(
            "Triage question",
            value="What is the most likely root cause?",
            height=110,
        )
        run = st.button("Run triage", type="primary", use_container_width=True)
        st.divider()
        st.caption("Demo workflow")
        st.markdown("- Select an incident\n- Run triage\n- Review citations\n- Inspect evidence")

    bundle = load_incident_bundle(selected)
    if "last_selected" not in st.session_state or st.session_state.last_selected != str(selected):
        st.session_state.last_selected = str(selected)
        st.session_state.report = analyze_incident(bundle, query=query)
    elif run:
        st.session_state.report = analyze_incident(bundle, query=query)

    report = st.session_state.report
    top_hypothesis = report.hypotheses[0] if report.hypotheses else None

    _render_header(bundle.title, bundle.summary, top_hypothesis.label if top_hypothesis else "No hypothesis")
    _render_metrics(bundle, report)

    analysis_tab, evidence_tab, artifacts_tab, benchmark_tab = st.tabs(
        ["Analysis", "Evidence", "Artifacts", "Benchmark"]
    )

    with analysis_tab:
        _render_analysis(report)

    with evidence_tab:
        _render_evidence(report)

    with artifacts_tab:
        _render_artifacts(bundle)

    with benchmark_tab:
        _render_benchmark()


def _render_header(title: str, summary: str, top_label: str) -> None:
    safe_title = escape(title)
    safe_summary = escape(summary)
    safe_top_label = escape(top_label)
    st.markdown(
        f"""
        <section class="tw-hero">
          <div>
            <p class="tw-eyebrow">Incident command view</p>
            <h1>{safe_title}</h1>
            <p class="tw-summary">{safe_summary}</p>
          </div>
          <div class="tw-status">
            <span>Leading hypothesis</span>
            <strong>{safe_top_label}</strong>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_metrics(bundle, report) -> None:
    top_confidence = report.hypotheses[0].confidence if report.hypotheses else 0.0
    artifact_counts = Counter(artifact.artifact_type.value for artifact in bundle.artifacts)
    risk_level = _risk_level(top_confidence)
    citation_count = len({citation for hypothesis in report.hypotheses for citation in hypothesis.citations})

    cols = st.columns(5)
    metrics = [
        ("Confidence", f"{top_confidence:.0%}", _confidence_label(top_confidence)),
        ("Risk Level", risk_level, "based on confidence"),
        ("Evidence", str(len(report.evidence)), "retrieved chunks"),
        ("Citations", str(citation_count), "unique sources"),
        ("Artifacts", str(len(bundle.artifacts)), f"{len(artifact_counts)} types"),
    ]
    for col, (label, value, caption) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="tw-metric">
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>{caption}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_analysis(report) -> None:
    left, right = st.columns([1.25, 0.75])

    with left:
        st.markdown("### Root-cause hypotheses")
        for index, hypothesis in enumerate(report.hypotheses, start=1):
            safe_label = escape(hypothesis.label)
            safe_rationale = escape(hypothesis.rationale)
            safe_citations = escape(", ".join(hypothesis.citations))
            st.markdown(
                f"""
                <div class="tw-card">
                  <div class="tw-card-title">
                    <span class="tw-rank">{index}</span>
                    <strong>{safe_label}</strong>
                    <em>{hypothesis.confidence:.0%}</em>
                  </div>
                  <div class="tw-bar"><span style="width:{hypothesis.confidence * 100:.0f}%"></span></div>
                  <p>{safe_rationale}</p>
                  <small>Citations: {safe_citations}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### Recommended fix plan")
        for step_number, step in enumerate(report.recommended_fix_plan, start=1):
            safe_step = escape(step)
            st.markdown(
                f"""
                <div class="tw-step">
                  <span>{step_number}</span>
                  <p>{safe_step}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("### Incident timeline")
        if report.timeline:
            for event in report.timeline:
                safe_timestamp = escape(event.timestamp)
                safe_message = escape(event.message)
                safe_citation = escape(event.citation)
                st.markdown(
                    f"""
                    <div class="tw-timeline">
                      <strong>{safe_timestamp}</strong>
                      <p>{safe_message}</p>
                      <small>{safe_citation}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No timestamped events found in cited evidence.")


def _render_evidence(report) -> None:
    st.markdown("### Retrieved evidence")
    rows = [
        {
            "citation": hit.chunk.citation,
            "artifact_type": hit.chunk.artifact_type.value,
            "score": hit.score,
            "matched_terms": ", ".join(hit.matched_terms),
        }
        for hit in report.evidence
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    for hit in report.evidence:
        with st.expander(f"{hit.chunk.citation} | score {hit.score}"):
            st.code(hit.chunk.text)
            st.caption("Matched terms: " + ", ".join(hit.matched_terms))


def _render_artifacts(bundle) -> None:
    st.markdown("### Incident artifacts")
    type_counts = Counter(artifact.artifact_type.value for artifact in bundle.artifacts)
    cols = st.columns(max(1, len(type_counts)))
    for col, (artifact_type, count) in zip(cols, sorted(type_counts.items())):
        safe_artifact_type = escape(artifact_type)
        with col:
            st.markdown(
                f"""
                <div class="tw-mini">
                  <span>{safe_artifact_type}</span>
                  <strong>{count}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

    for artifact in bundle.artifacts:
        line_count = len(artifact.text.splitlines())
        with st.expander(f"{artifact.path} | {artifact.artifact_type.value} | {line_count} lines"):
            st.code(artifact.text)


def _render_benchmark() -> None:
    st.markdown("### Evaluation snapshot")
    if not EVAL_CASES_PATH.exists():
        st.warning("No evaluation cases found.")
        return

    cases = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))
    results = []
    correct = 0
    for case in cases:
        case_bundle = load_incident_bundle(PROJECT_ROOT / case["incident_dir"])
        case_report = analyze_incident(case_bundle, query=case.get("query", "What is the most likely root cause?"))
        top_label = case_report.hypotheses[0].label if case_report.hypotheses else ""
        expected = [keyword.lower() for keyword in case["expected_cause_keywords"]]
        passed = any(keyword in top_label.lower() for keyword in expected)
        correct += int(passed)
        results.append(
            {
                "incident": case_bundle.incident_id,
                "expected": ", ".join(expected),
                "predicted": top_label,
                "passed": passed,
                "citations": len(case_report.hypotheses[0].citations) if case_report.hypotheses else 0,
            }
        )

    accuracy = correct / len(results) if results else 0.0
    cols = st.columns(3)
    cols[0].metric("Root-cause accuracy", f"{accuracy:.0%}")
    cols[1].metric("Benchmark cases", len(results))
    cols[2].metric("Passing cases", correct)
    st.dataframe(results, use_container_width=True, hide_index=True)
    st.caption("Benchmark checks whether the top-ranked hypothesis matches known root-cause keywords.")


def _risk_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "High"
    if confidence >= 0.5:
        return "Medium"
    return "Needs review"


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "strong signal"
    if confidence >= 0.5:
        return "moderate signal"
    return "low signal"


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
          padding-top: 2rem;
          max-width: 1320px;
        }
        .tw-hero {
          display: flex;
          justify-content: space-between;
          gap: 24px;
          padding: 28px 30px;
          border: 1px solid #dbe3ee;
          border-radius: 8px;
          background: #ffffff;
          box-shadow: 0 14px 40px rgba(15, 23, 42, 0.06);
          margin-bottom: 18px;
        }
        .tw-eyebrow {
          margin: 0 0 8px 0;
          color: #2563eb;
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0;
          text-transform: uppercase;
        }
        .tw-hero h1 {
          margin: 0;
          color: #0f172a;
          font-size: 30px;
          line-height: 1.15;
        }
        .tw-summary {
          margin: 12px 0 0 0;
          color: #475569;
          font-size: 15px;
          max-width: 860px;
        }
        .tw-status {
          min-width: 260px;
          padding: 18px;
          border-radius: 8px;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
        }
        .tw-status span,
        .tw-metric span,
        .tw-mini span {
          display: block;
          color: #64748b;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
        }
        .tw-status strong {
          display: block;
          margin-top: 10px;
          color: #0f172a;
          font-size: 19px;
          line-height: 1.2;
        }
        .tw-metric,
        .tw-mini {
          padding: 18px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          min-height: 110px;
        }
        .tw-metric strong,
        .tw-mini strong {
          display: block;
          margin-top: 8px;
          color: #0f172a;
          font-size: 28px;
          line-height: 1;
        }
        .tw-metric small {
          display: block;
          margin-top: 9px;
          color: #64748b;
        }
        .tw-card,
        .tw-step,
        .tw-timeline {
          padding: 18px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          margin-bottom: 12px;
        }
        .tw-card-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .tw-card-title strong {
          flex: 1;
          color: #0f172a;
          font-size: 17px;
        }
        .tw-card-title em {
          color: #2563eb;
          font-style: normal;
          font-weight: 800;
        }
        .tw-rank,
        .tw-step span {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          border-radius: 999px;
          background: #dbeafe;
          color: #1d4ed8;
          font-weight: 800;
        }
        .tw-card p,
        .tw-step p,
        .tw-timeline p {
          margin: 12px 0 8px 0;
          color: #334155;
        }
        .tw-card small,
        .tw-timeline small {
          color: #64748b;
        }
        .tw-bar {
          height: 9px;
          margin-top: 14px;
          overflow: hidden;
          border-radius: 999px;
          background: #e2e8f0;
        }
        .tw-bar span {
          display: block;
          height: 100%;
          border-radius: 999px;
          background: #2563eb;
        }
        .tw-step {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }
        .tw-step p {
          margin: 2px 0 0 0;
        }
        .tw-timeline {
          border-left: 4px solid #2563eb;
        }
        .tw-timeline strong {
          color: #0f172a;
          font-size: 13px;
        }
        div[data-testid="stMetric"] {
          padding: 12px 14px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
