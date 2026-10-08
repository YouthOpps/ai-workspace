# YouthOpps AI Workspace

This repository is **exclusively for reusable AI agent skills and development-workspace setup**. Read the relevant `SKILL.md` when authoring or maintaining a skill; other skills added later are not automatically active.

## Repository boundaries
- `data-pipeline/`: manifests, adapters, tests, `fetch-<source-id>` Actions.
- `data-source/`: published source snapshots and `catalog.json`; no Actions.
- `website/`: static frontend, including its own pinned `data-source` submodule.

These are Git submodules, provided as read-only structural/code references. Run `git submodule update --init --recursive` to initialize the workspace. Only adjust a submodule pointer when explicitly asked to maintain the workspace layout. Do not commit or push modifications inside any submodule while working on this repository.

## Scope boundary
- **Allowed here:** author, review, test and version skills; maintain AI workspace documentation and submodule wiring.
- **Forbidden here:** selecting, starting, labeling, implementing, testing or closing GitHub source issues; modifying source adapters/website/data snapshots; triggering collection Actions; deploying any integration.
- A skill may document those operations for a **future, separately authorized integration task**, but its mere presence in this repo is not permission to perform them.
- No issue, including an issue mentioned as an example, is considered assigned to this workspace.
