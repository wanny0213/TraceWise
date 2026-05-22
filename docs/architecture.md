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

The first retriever is local and deterministic. It scores chunks using token overlap with inverse-document-frequency weighting. This keeps tests and demos stable before adding an LLM or embedding provider.

## Triage Analysis

The analyzer currently uses evidence signals for common incident classes:

- configuration regression
- API contract mismatch
- dependency or version regression
- timeout or upstream outage
- test failure regression

The ranked hypotheses include confidence, rationale, and citations. The analyzer also extracts timestamped lines into a timeline.

## Evaluation

`eval_cases.json` defines benchmark incidents and expected root-cause keywords. The evaluation CLI reports root-cause accuracy and per-case citations.

Future evaluation should add:

- retrieval recall at `k`
- citation precision
- timeline extraction quality
- patch recommendation usefulness
