---
name: adapter
description: Develop, review or test YouthOpps source adapters under the required standalone two-file architecture. Use for source integration and connector tasks in data-pipeline.
---

# YouthOpps Adapter

Provider-independent instructions: follow the shared [agent scope](../../AGENTS.md#provider-independent-scope), including equivalent tools and independent review.

Use `adapter` in authored code and prose, interpreting source integration/connector requests accordingly. Use one stable, filesystem-safe lowercase kebab-case source slug in paths, workflows and output.

## Task routing

Read [workspace rules](../../AGENTS.md) once. For review, inspect the requested base/head without branch alignment; for implementation or maintenance, use the corresponding [workflow route](../../docs/WORKFLOW.md). Skill maintenance does not authorize collection or publication.

- **Develop/refactor:** read [contract](references/contract.md) and [development](references/development.md).
- **Review/QA:** read the contract for runtime or data changes and [testing](references/testing.md) for acceptance evidence. Static review does not imply that a live test passed.
- **Rules maintenance:** read the affected references and their consumers; preserve acceptance invariants and verify public reference links.

## Mandatory architecture — acceptance gate

This architecture applies to development, fixes, refactoring, synchronization and reviews. Only an explicit user change to the architecture permits a deviation; generic cleanup, optimization or reuse requests do not.

- Each `adapters/<pretty-source-name>/` contains exactly `adapter.py` and `test_adapter.py`. The implementation contains source URLs, transport/pacing, parsing, normalization, validation, metadata and publication. Keep source notes in that file.
- Each folder must run independently when copied outside the repository. Python standard library only; the test may additionally import its own adapter. No third-party, cross-folder, root, dynamically downloaded or generated shared code. Intentional duplication between adapters is allowed; no shared framework, dispatcher, registry or package.
- The only application directories are `adapters/` and `.github/workflows/`. Root `AGENTS.md`, existing `README.md`, `.gitignore` and Git metadata are allowed. No extra source/config/schema/data/doc/fixture/test files, manifests, lockfiles, shared infrastructure, bytecode or temporary output in the delivered tree.
- Each implemented adapter has exactly one `.github/workflows/fetch-<pretty-source-name>.yml`, the only executable exception outside adapter folders. It may check out code, select Python and obtain `DATA_SOURCE_TOKEN`; its application command is only `python -B adapters/<pretty-source-name>/adapter.py --publish`. No tests, formatter steps, dependency installation, shared publication logic, matrices or reusable dispatch pipelines.
- `test_adapter.py` has exactly one live, non-publishing collection test. It retrieves real nonempty records, validates them and emits the actual complete result as one JSON document on stdout, with diagnostics on stderr. No publication token, output files or mocks/fixtures substituting for real retrieval.
- Only implemented, explicitly authorized sources belong in the repository. Derive current inventory from the checkout; do not restore historical candidates or add placeholder folders/Actions. New sources require assigned development and a passing live test.

Before editing, establish the complete file inventory and architecture compliance, including imports and workflows. Use tool-side checks with concise output; inspect suspected violations in detail. Before handoff, recheck changed paths and inventory differences against that baseline; rescan fully if no reliable baseline exists or structure, imports or workflow routing changed. Every structural violation blocks acceptance even if tests pass. Report violations outside the authorized repair scope. Do not add a shared validator or test suite to data-pipeline.

Runtime/data behavior is defined once in [contract](references/contract.md). Apply [code style](../../docs/CODE_STYLE.md) without relaxing this architecture. Both data-source checkouts remain publication-only under workspace rules.
