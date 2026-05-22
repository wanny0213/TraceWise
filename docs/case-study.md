# Case Study: Auth Regression

## Problem

After a deployment, all login requests begin returning 500 errors. The incident bundle contains runtime logs, a stack trace, and the service config.

## TraceWise Output

Top root-cause hypothesis:

```text
configuration regression
```

The report cites three evidence sources:

- `runtime.log:1-7`
- `service.yaml:1-8`
- `stacktrace.txt:1-8`

## Why The Hypothesis Is Correct

The runtime log says the service is missing `AUTH_JWT_SECRET`. The stack trace shows token creation fails while building the JWT signer. The config still contains `AUTH_TOKEN_SECRET`, and the manifest notes the deployment renamed the secret lookup.

Together, those artifacts support a specific diagnosis: the code now expects a renamed secret that production config does not provide.

## Recommended Fix

TraceWise recommends:

- compare runtime configuration against the last healthy deployment
- add startup validation for required environment variables
- add a regression test for missing required configuration

## Engineering Value

This case demonstrates the core product idea: incident analysis should be grounded in cited evidence, not a vague LLM-generated explanation.
