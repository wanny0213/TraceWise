# Project Plan

## MVP

- Load incident bundles from disk.
- Chunk logs, stack traces, config, code, and test output.
- Retrieve evidence for a triage query.
- Rank root-cause hypotheses.
- Produce cited reports and timeline events.
- Evaluate on demo incidents.

## Recruiter Polish Milestones

1. Add screenshots and a case-study section to the README.
2. Add LLM synthesis with strict citation grounding.
3. Add GitHub Actions ingestion for failed CI runs.
4. Record a short demo video.
5. Add patch proposal mode with generated regression tests.
6. Add external embedding provider support.

## Stretch Goal

Patch proposal mode:

1. Identify suspected source files.
2. Propose a minimal fix.
3. Generate a regression test.
4. Explain why the patch addresses the cited evidence.
