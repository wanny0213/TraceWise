from tracewise.analysis.triage import analyze_incident
from tracewise.ingestion.bundles import load_incident_bundle


def test_triage_ranks_configuration_regression_for_auth_demo():
    bundle = load_incident_bundle("incidents/demo-auth-regression")

    report = analyze_incident(bundle, query="Why did login fail after deploy?")

    assert report.hypotheses
    assert report.hypotheses[0].label == "configuration regression"
    assert report.hypotheses[0].citations
    assert report.timeline
    assert report.recommended_fix_plan


def test_triage_ranks_timeout_for_payment_demo():
    bundle = load_incident_bundle("incidents/demo-payment-timeout")

    report = analyze_incident(bundle, query="Why did checkout payments fail?")

    assert report.hypotheses
    assert report.hypotheses[0].label == "timeout or upstream outage"
    assert any("gateway.log" in citation for citation in report.hypotheses[0].citations)


def test_triage_supports_vector_retriever():
    bundle = load_incident_bundle("incidents/demo-auth-regression")

    report = analyze_incident(
        bundle,
        query="Why did login fail after deploy?",
        retriever_mode="vector",
    )

    assert report.hypotheses
    assert report.hypotheses[0].label == "configuration regression"
