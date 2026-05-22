from tracewise.ingestion.bundles import load_incident_bundle
from tracewise.ingestion.chunking import chunk_bundle
from tracewise.retrieval.keyword import KeywordRetriever


def test_keyword_retriever_finds_missing_secret_evidence():
    bundle = load_incident_bundle("incidents/demo-auth-regression")
    retriever = KeywordRetriever(chunk_bundle(bundle.incident_id, bundle.artifacts))

    hits = retriever.search("missing AUTH_JWT_SECRET environment variable", top_k=3)

    assert hits
    assert "AUTH_JWT_SECRET" in hits[0].chunk.text
    assert hits[0].chunk.citation
