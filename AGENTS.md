# YouthOpps AI Workspace

This repository hosts reusable AI agent skills. Read the relevant `SKILL.md` before acting; other skills added later are not automatically active.

## Repository boundaries
- `data-pipeline/`: manifests, adapters, tests, `fetch-<source-id>` Actions.
- `data-source/`: published source snapshots and `catalog.json`; no Actions.
- `website/`: static frontend, including its own pinned `data-source` submodule.

These are Git submodules. Run `git submodule update --init --recursive`. A workspace commit only pins submodule SHAs; changes inside a submodule need their own commit and push. Do not modify unrelated repositories or advance gitlinks casually.

## Task execution
Use `skills/integration-development/SKILL.md` for one source integration and `skills/integration-testing/SKILL.md` for its independent QA. Select exactly one assigned issue (e.g. YouthOpps/data-pipeline#11), make sure its label is `in progress`, and never pick up a second task before its acceptance or explicit blocker report. A blocked source stays blocked; never misreport successful integration.

Do not bypass publisher access restrictions. Cap outbound requests to any one target at 10 requests per rolling minute, across retries, probes, redirects and concurrent workers. Respect stronger publisher limits.
