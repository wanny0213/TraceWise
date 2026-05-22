# Architecture

TraceWise is organized around a simple evidence pipeline:

```text
incident bundle -> artifacts -> chunks -> retriever -> triage analyzer -> report
```

## Incident Bundle

Each bundle has an `incident.json` manifest plus artifact files. The manifest names each artifact and gives its type:

- `log`
- `stack_trace`
- `code`
- `config`
- `test_output`
- `note`

This makes the demo reproducible and keeps evaluation cases stable.

## Chunking

Artifacts are split into line-aware chunks. Every chunk preserves:

- incident id
- artifact id
- artifact type
- path
- start line
- end line

The report can cite evidence as `path:start-end`.

## Retrieval

TraceWise currently supports two deterministic retrievers:

- `keyword`: token overlap with inverse-document-frequency weighting
- `vector`: dependency-free TF-IDF cosine similarity

Both modes are local, reproducible, and covered by tests. This keeps the project measurable before adding external embedding models.

## Triage Analysis

The analyzer currently uses evidence signals for common incident classes:

- configuration regression
- API contract mismatch
- dependency or version regression
- timeout or upstream outage
- test failure regression

The ranked hypotheses include confidence, rationale, and citations. The analyzer also extracts timestamped lines into a timeline.

## Evaluation

`eval_cases.json` defines benchmark incidents and expected root-cause keywords. The evaluation CLI reports root-cause accuracy and per-case citations. It can also compare `keyword` and `vector` retrieval:

```bash
python -m tracewise.evals.cli eval_cases.json --retriever compare
```

Future evaluation should add:

- retrieval recall at `k`
- citation precision
- timeline extraction quality
- patch recommendation usefulness
