from __future__ import annotations

from pathlib import Path

import streamlit as st

from tracewise.analysis.triage import analyze_incident
from tracewise.ingestion.bundles import load_incident_bundle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INCIDENTS_DIR = PROJECT_ROOT / "incidents"


def main() -> None:
    st.set_page_config(page_title="TraceWise", page_icon="TW", layout="wide")

    st.title("TraceWise")
    st.caption("AI incident triage with cited root-cause analysis")

    incident_dirs = sorted(
        path for path in INCIDENTS_DIR.iterdir() if path.is_dir() and (path / "incident.json").exists()
    )
    if not incident_dirs:
        st.error("No incident bundles found.")
        return

    with st.sidebar:
        st.header("Incident")
        selected = st.selectbox("Bundle", incident_dirs, format_func=lambda path: path.name)
        query = st.text_area(
            "Triage question",
            value="What is the most likely root cause?",
            height=90,
        )
        run = st.button("Run triage", type="primary", use_container_width=True)

    bundle = load_incident_bundle(selected)
    if "last_selected" not in st.session_state or st.session_state.last_selected != str(selected):
        st.session_state.last_selected = str(selected)
        st.session_state.report = analyze_incident(bundle, query=query)
    elif run:
        st.session_state.report = analyze_incident(bundle, query=query)

    report = st.session_state.report

    st.subheader(bundle.title)
    if bundle.summary:
        st.write(bundle.summary)

    summary_col, metric_col = st.columns([3, 1])
    with summary_col:
        st.markdown("### Executive Summary")
        st.info(report.executive_summary)
    with metric_col:
        confidence = report.hypotheses[0].confidence if report.hypotheses else 0
        st.metric("Top Confidence", f"{confidence:.0%}")
        st.metric("Evidence Chunks", len(report.evidence))

    left, right = st.columns([1.1, 0.9])

    with left:
        st.markdown("### Root-Cause Hypotheses")
        for index, hypothesis in enumerate(report.hypotheses, start=1):
            with st.container(border=True):
                st.markdown(f"**{index}. {hypothesis.label}**")
                st.progress(hypothesis.confidence)
                st.write(hypothesis.rationale)
                st.caption("Citations: " + ", ".join(hypothesis.citations))

        st.markdown("### Recommended Fix Plan")
        for step in report.recommended_fix_plan:
            st.checkbox(step, value=False)

    with right:
        st.markdown("### Timeline")
        if report.timeline:
            for event in report.timeline:
                with st.container(border=True):
                    st.caption(event.timestamp)
                    st.write(event.message)
                    st.caption(event.citation)
        else:
            st.caption("No timestamped events found in cited evidence.")

    st.markdown("### Evidence")
    for hit in report.evidence:
        with st.expander(f"{hit.chunk.citation} · score {hit.score}"):
            st.code(hit.chunk.text)
            st.caption("Matched terms: " + ", ".join(hit.matched_terms))


if __name__ == "__main__":
    main()
