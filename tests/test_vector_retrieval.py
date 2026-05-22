from tracewise.ingestion.bundles import load_incident_bundle
from tracewise.ingestion.chunking import chunk_bundle
from tracewise.retrieval.vector import LocalVectorRetriever


def test_local_vector_retriever_finds_timeout_evidence():
    bundle = load_incident_bundle("incidents/demo-payment-timeout")
    retriever = LocalVectorRetriever(chunk_bundle(bundle.incident_id, bundle.artifacts))

    hits = retriever.search("upstream gateway timeout checkout failure", top_k=3)

    assert hits
    assert "gateway" in hits[0].chunk.text.lower()
    assert hits[0].score > 0
