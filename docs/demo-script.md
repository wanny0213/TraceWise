# Demo Script

This is a short walkthrough for recruiters or interviewers.

## 1. Open the Dashboard

```bash
streamlit run tracewise/ui/streamlit_app.py
```

Choose `demo-auth-regression` from the sidebar.

## 2. Run Triage

Use the default question:

```text
What is the most likely root cause?
```

TraceWise should rank `configuration regression` as the top cause.

Point out:

- confidence score
- cited artifacts
- timeline events
- recommended fix checklist
- retrieved evidence chunks

## 3. Explain the Evidence

The auth incident includes:

- a runtime log showing `AUTH_JWT_SECRET` is missing
- a stack trace showing token signing fails
- a service config showing the old secret name still exists

TraceWise connects those signals into a root-cause hypothesis instead of giving a generic summary.

## 4. Run the Benchmark

```bash
python -m tracewise.evals.cli eval_cases.json
```

The benchmark checks whether the top-ranked root cause matches known expected causes for the demo incidents.

Then compare retrieval modes:

```bash
python -m tracewise.evals.cli eval_cases.json --retriever compare
```

Point out that TraceWise can evaluate retrieval choices instead of assuming one approach is better.

## 5. Interview Talking Points

- The project starts deterministic so behavior is testable before adding an LLM.
- Every answer carries citations back to incident artifacts.
- The evaluation CLI makes quality measurable instead of subjective.
- The architecture can grow into external embeddings, GitHub CI ingestion, and patch proposal mode.
