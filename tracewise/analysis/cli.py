from __future__ import annotations

import argparse
import json

from tracewise.analysis.triage import analyze_incident
from tracewise.ingestion.bundles import load_incident_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TraceWise triage on an incident bundle.")
    parser.add_argument("incident_dir")
    parser.add_argument("--query", default="What is the most likely root cause?")
    parser.add_argument("--retriever", choices=["keyword", "vector"], default="keyword")
    args = parser.parse_args()

    bundle = load_incident_bundle(args.incident_dir)
    report = analyze_incident(bundle, query=args.query, retriever_mode=args.retriever)
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
