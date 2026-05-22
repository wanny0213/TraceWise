from __future__ import annotations

from tracewise.core.models import EvidenceChunk, IncidentArtifact


def chunk_artifact(
    incident_id: str,
    artifact: IncidentArtifact,
    max_lines: int = 12,
    overlap: int = 2,
) -> list[EvidenceChunk]:
    lines = artifact.text.splitlines()
    if not lines:
        return []

    chunks = []
    step = max(1, max_lines - overlap)
    for start in range(0, len(lines), step):
        end = min(len(lines), start + max_lines)
        chunk_lines = lines[start:end]
        chunk_id = f"{artifact.artifact_id}:{start + 1}-{end}"
        chunks.append(
            EvidenceChunk(
                chunk_id=chunk_id,
                incident_id=incident_id,
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                path=artifact.path,
                text="\n".join(chunk_lines),
                start_line=start + 1,
                end_line=end,
            )
        )
        if end == len(lines):
            break
    return chunks


def chunk_bundle(incident_id: str, artifacts: list[IncidentArtifact]) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for artifact in artifacts:
        chunks.extend(chunk_artifact(incident_id, artifact))
    return chunks
