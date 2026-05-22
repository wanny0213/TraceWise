from __future__ import annotations

import argparse
import json
from pathlib import Path

from tracewise.analysis.triage import analyze_incident
from tracewise.ingestion.bundles import load_incident_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TraceWise on incident bundles.")
    parser.add_argument("cases_file", help="JSON file containing evaluation cases.")
    parser.add_argument("--retriever", choices=["keyword", "vector", "compare"], default="keyword")
    args = parser.parse_args()

    cases = json.loads(Path(args.cases_file).read_text(encoding="utf-8"))
    if args.retriever == "compare":
        output = {
            "retrievers": {
                mode: _evaluate_cases(cases, retriever_mode=mode)
                for mode in ["keyword", "vector"]
            }
        }
    else:
        output = _evaluate_cases(cases, retriever_mode=args.retriever)

    print(json.dumps(output, indent=2))


def _evaluate_cases(cases: list[dict], retriever_mode: str) -> dict:
    results = []
    correct = 0
    for case in cases:
        bundle = load_incident_bundle(case["incident_dir"])
        report = analyze_incident(
            bundle,
            query=case.get("query", "What is the most likely root cause?"),
            retriever_mode=retriever_mode,
        )
        top_label = report.hypotheses[0].label if report.hypotheses else ""
        expected = [keyword.lower() for keyword in case["expected_cause_keywords"]]
        is_correct = any(keyword in top_label.lower() for keyword in expected)
        correct += int(is_correct)
        results.append(
            {
                "incident_id": bundle.incident_id,
                "top_label": top_label,
                "expected_keywords": expected,
                "correct": is_correct,
                "citations": report.hypotheses[0].citations if report.hypotheses else [],
            }
        )

    return {
        "retriever": retriever_mode,
        "cases": len(results),
        "root_cause_accuracy": round(correct / len(results), 3) if results else 0.0,
        "results": results,
    }


if __name__ == "__main__":
    main()
