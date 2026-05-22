from tracewise.ingestion.bundles import load_incident_bundle


def test_load_incident_bundle_reads_manifest_and_artifacts():
    bundle = load_incident_bundle("incidents/demo-auth-regression")

    assert bundle.incident_id == "demo-auth-regression"
    assert bundle.title
    assert len(bundle.artifacts) == 3
    assert "AUTH_JWT_SECRET" in bundle.artifacts[0].text
