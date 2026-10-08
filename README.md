# YouthOpps AI Workspace

Reusable AI agent skills and an isolated, submodule-based workspace for the [YouthOpps](https://youthopps.org) project.

## Checkout

```sh
git clone https://github.com/YouthOpps/ai-workspace.git
cd ai-workspace
git submodule update --init --recursive
```

## Submodules

| Local directory | Repository | Purpose |
|---|---|---|
| `data-pipeline/` | [data-pipeline](https://github.com/YouthOpps/data-pipeline) | Adapters, validation and source-specific Actions |
| `data-source/` | [data-source](https://github.com/YouthOpps/data-source) | Published source JSON and catalog |
| `website/` | [youthopps.github.io](https://github.com/YouthOpps/youthopps.github.io) | Website, consuming data-source |

Submodules are pinned for workspace configuration. During **skill authoring here**, they are read-only. A **separately authorized integration-development task** can work on an issue branch *inside* the `data-pipeline` submodule and open a PR there, without updating `ai-workspace`'s gitlink or changing `data-source`/`website`. Only a different maintainer merges that PR. Skills/workspace maintenance does not itself start any integration task.

## Skills

- [Integration development](skills/integration-development/SKILL.md): choose Python/Node.js per source, deliver a clean data-pipeline-only commit, and open an issue-linked **unmerged** PR after QA.
- [Integration testing](skills/integration-testing/SKILL.md): independent completeness and safety gate, sandbox-first; online environment second; GitHub Actions last resort.

The skills also define an **unsolvable** outcome when no permitted data retrieval path exists, and one independent GitHub Action per adapter, writing validated records to `data-source/sources/<connector-id>/opportunities.json` and collection status/last successful retrieval to the sibling `metadata.json` (never root `data-source/sources.json`). These are *instructions*, not implemented application changes.

Read [AGENTS.md](AGENTS.md) before working. Additional skills may be added later. No issue or source is automatically assigned by the workspace. Skills are reusable instructions for **future, separately authorized execution**; creating or editing a skill does not authorize running it.
