from __future__ import annotations

import json
from pathlib import Path

from tracewise.core.models import ArtifactType, IncidentArtifact, IncidentBundle


ARTIFACT_SUFFIX_TYPES = {
    ".log": ArtifactType.LOG,
    ".trace": ArtifactType.STACK_TRACE,
    ".stacktrace": ArtifactType.STACK_TRACE,
    ".py": ArtifactType.CODE,
    ".js": ArtifactType.CODE,
    ".ts": ArtifactType.CODE,
    ".tsx": ArtifactType.CODE,
    ".java": ArtifactType.CODE,
    ".yaml": ArtifactType.CONFIG,
    ".yml": ArtifactType.CONFIG,
    ".json": ArtifactType.CONFIG,
    ".ini": ArtifactType.CONFIG,
    ".cfg": ArtifactType.CONFIG,
    ".out": ArtifactType.TEST_OUTPUT,
    ".txt": ArtifactType.NOTE,
    ".md": ArtifactType.NOTE,
}


def load_incident_bundle(path: str | Path) -> IncidentBundle:
    incident_dir = Path(path)
    manifest_path = incident_dir / "incident.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing incident manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = []
    for artifact in manifest.get("artifacts", []):
        artifact_path = incident_dir / artifact["path"]
        artifact_type = ArtifactType(artifact.get("type") or _infer_artifact_type(artifact_path))
        artifacts.append(
            IncidentArtifact(
                artifact_id=artifact.get("id", artifact_path.stem),
                artifact_type=artifact_type,
                path=artifact["path"],
                text=artifact_path.read_text(encoding="utf-8"),
            )
        )

    return IncidentBundle(
        incident_id=manifest["incident_id"],
        title=manifest["title"],
        summary=manifest.get("summary", ""),
        artifacts=artifacts,
    )


def _infer_artifact_type(path: Path) -> ArtifactType:
    return ARTIFACT_SUFFIX_TYPES.get(path.suffix.lower(), ArtifactType.NOTE)
