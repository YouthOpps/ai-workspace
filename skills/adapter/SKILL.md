---
name: adapter
description: Develop and independently verify one YouthOpps source adapter. Accept "integration", "integrate", and "connector" as requests for adapter work; use adapter terminology consistently.
---

# YouthOpps Adapter

**Terminology:** Always call the unit of work an **adapter**. Treat user phrases such as "integration", "integrate a source", or "connector" as equivalent requests, without creating separate skills. Use `source-id` for the configured publisher/source identity and `adapter` for its collection implementation.

This is **one skill** with two task references:
- [Adapter Development](references/development.md): source research, implementation, selected Python/Node.js runtime, publication contract, PR handoff, blocked/unsolvable outcomes.
- [Adapter Testing](references/testing.md): independent QA, source coverage, safety, sandbox-first testing, acceptance and rejection.

## Activation and scope

1. Read [AGENTS.md](../../AGENTS.md) and [docs/WORKFLOW.md](../../docs/WORKFLOW.md) before execution.
2. **Workspace maintenance:** edit skills and workspace documentation only; no project issue development or production Action runs.
3. **Assigned adapter issue:** operate on a single explicitly assigned `data-pipeline` issue. Fetch current `origin/main` inside its submodule and branch from it; never commit the workspace gitlink. Keep `data-source` and `website` read-only during development.
4. Use the development reference for implementation and the testing reference for an independent QA gate. A developer cannot self-approve QA; accurately report when separate agents are unavailable.
5. Deliver only a clean, issue-linked **data-pipeline PR**, left **open and unmerged** for a maintainer. Never claim that passing tests proves production publication.

## Non-negotiable controls

- One issue and one project at a time; all agent artifacts and project communication in **English**.
- Review the full affected code, existing tests and authoritative docs; prefer minimal coherent changes, updates to existing documentation and one or two focused adapter tests when sufficient.
- Retrieve only genuine publisher opportunities using permitted access; never invent records or bypass restrictions.
- At most **10 requests per target in any rolling 60 seconds**, including redirects/retries, and at least six seconds apart; honor stricter publisher rules.
- One source-specific `fetch-<source-id>` Action; a shared adapter implementation can serve several sources without duplicating code.
- After maintainer merge, the Action is responsible for `data-source/sources/<source-id>/opportunities.json` and `metadata.json`, plus consistent `catalog.json` status. On failure preserve the last good opportunities and success timestamp, and publish sanitized error metadata where a previously integrated source exists.
- If no lawful workable acquisition route exists, document the evidence on the issue and mark it `unsolvable`; do not publish an unintegrated source.

Select the reference relevant to the current phase; do not load both in full when only one is needed.
