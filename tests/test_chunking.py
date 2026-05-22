from tracewise.ingestion.bundles import load_incident_bundle
from tracewise.ingestion.chunking import chunk_bundle


def test_chunk_bundle_preserves_citation_metadata():
    bundle = load_incident_bundle("incidents/demo-auth-regression")
    chunks = chunk_bundle(bundle.incident_id, bundle.artifacts)

    assert chunks
    first = chunks[0]
    assert first.path == "runtime.log"
    assert first.start_line == 1
    assert first.end_line >= first.start_line
    assert ":" in first.citation
