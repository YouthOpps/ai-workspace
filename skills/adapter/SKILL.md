---
name: adapter
description: Develop or test one YouthOpps source adapter. Understand user terms integration, connector, and integration testing, but always use adapter terminology.
---

# YouthOpps Adapter

**Terminology:** Say **adapter** in all authored code, documentation and discussion. Interpret "integration" or "connector" as an adapter request. The literal repository folder is `adaptors/` (project path convention). Use one stable, filesystem-safe, lower-kebab-case `<pretty-source-name>` consistently in paths, Action names and output.

This is **one skill**, with phase-specific references:
- [Development](references/development.md) — source research, implementation, runtime choice, publication, issue branch and unmerged PR.
- [Testing](references/testing.md) — independent QA, live coverage and safe test-environment escalation.

## Activation

1. Read [AGENTS.md](../../AGENTS.md) and [docs/WORKFLOW.md](../../docs/WORKFLOW.md).
2. Maintaining this workspace only changes skill/docs/setup; it never authorizes an adapter issue or production Action.
3. For a separately assigned adapter issue, fetch and branch from the target `data-pipeline` repository's current `origin/main` **without committing the workspace gitlink**. Work on one issue/project only; keep `data-source` and `website` read-only. Never open a `data-source` PR or commit there directly.
4. Use the development reference for code and the testing reference for independent QA. Leave the issue-linked `data-pipeline` PR open and **unmerged** for the maintainer.

## Adapter and output contract

```text
data-pipeline/
  adaptors/<pretty-source-name>/
    adapter.js                 # or adapter.py; one implementation file preferred
    adapter.test.js            # or test_adapter.py; optional, max one test file
  .github/workflows/
    fetch-<pretty-source-name>.yml

data-source/
  datas/<pretty-source-name>/
    data.json                  # last successfully validated opportunity records
    metadata.json              # latest run result, explanation, timestamps
                             # no catalog.json or aggregate index
```

- One **independent GitHub Action per adapter**. It executes the script/class in its own folder using the chosen **Node.js or Python** runtime; no other adapter is fetched by that Action.
- The adapter file contains its own publisher URLs, source details, extraction rules and collection code. Add extra files **only when necessary**, never merely to split simple logic. No separate per-adapter source-configuration JSON. Shared infrastructure may validate and publish results without taking ownership of adapter-specific configuration.
- `data-source` is **publication-only**: its commits come exclusively from authorized `data-pipeline` Actions or exceptional manual administrator intervention. Adapter developers/QA must never push, commit directly, or open PRs there.
- After maintainer merge, a successful Action writes validated actual source records to `data.json` and records `status: "success"` in `metadata.json`. A failed run records `status: "fail"`, a sanitized error/explanation and UTC date/time; it **does not replace or erase the last-good `data.json`** or previous success timestamp. The adapter's `metadata.json` is the authoritative run-status record; **never create or update `data-source/catalog.json`**.
- Do not introduce a root-level `sources.json` or `catalog.json` in `data-source`. An adapter never successfully integrated is not published as an empty source folder. Consumer-side data discovery must be addressed by its own approved project design, not by recreating an aggregate catalog.
- Keep source access permitted and non-aggressive: at most 10 requests per rolling minute per target (including retries/redirects), with at least 6 seconds between requests; honor stricter limits. No synthetic opportunities.
- Each adapter may have **one test file in its own folder** (`adapter.test.js` or `test_adapter.py`), executed as one test entry point containing all necessary scenarios. Extend shared tests for shared behavior; never make separate per-implementation test files. Keep adapter-local documentation concise, code clean and compatibility layers only when truly required.

Read only the reference needed for the task phase.
