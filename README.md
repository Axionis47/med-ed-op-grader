# Med-Ed OP Grader

AWS-native, rubric-agnostic grader for oral H&Ps (audio→evidence-linked scores).
This repo hosts two SPAs (Instructor & Student), an API (FastAPI on Lambda),
prompts/schemas, infra as code, and golden tests.

## Getting started
1) Configure AWS SSO (see `/docs/DEMO_RUNBOOK.md`).
2) `make bootstrap` (installs CLIs & hooks).
3) Create an AWS profile via SSO and run `aws sts get-caller-identity`.

