# YouthOpps AI Workspace

This repository is **exclusively for reusable AI agent skills and development-workspace setup**. Read the relevant `SKILL.md` when authoring or maintaining a skill; other skills added later are not automatically active.

## Repository boundaries
- `data-pipeline/`: manifests, adapters, tests, `fetch-<source-id>` Actions.
- `data-source/`: published source snapshots and `catalog.json`; no Actions.
- `website/`: static frontend, including its own pinned `data-source` submodule.

These are Git submodules. Run `git submodule update --init --recursive` to initialize the workspace. During **skill/workspace maintenance**, treat the submodules as read-only, and only adjust gitlinks if explicitly asked. During a **separately authorized integration execution**, development may happen in an issue-specific branch **inside the `data-pipeline` submodule**. Push commits there and open a PR in `YouthOpps/data-pipeline`; never include its changed gitlink in an `ai-workspace` commit, and never merge the PR yourself.

## Scope boundary
- **Allowed here:** author, review, test and version skills; maintain AI workspace documentation and submodule wiring.
- **Forbidden here:** selecting, starting, labeling, implementing, testing or closing GitHub source issues; modifying source adapters/website/data snapshots; triggering collection Actions; deploying any integration.
- A skill may document those operations for a **future, separately authorized integration task**, but its mere presence in this repo is not permission to perform them. In such a task, choose Node.js or Python based on the source, keep connector changes limited to `data-pipeline`, remove unused/dead/back-compat artifacts, open an issue-linked PR and leave merging to someone else.
- No issue, including an issue mentioned as an example, is considered assigned to this workspace.
