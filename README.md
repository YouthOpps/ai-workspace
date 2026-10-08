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
| `data-pipeline/` | [data-pipeline](https://github.com/YouthOpps/data-pipeline) | `adaptors/<pretty-source-name>/adapter.js` or `adapter.py`, plus one Action per adapter |
| `data-source/` | [data-source](https://github.com/YouthOpps/data-source) | Published `datas/<pretty-source-name>/{data,metadata}.json` only; automation/admin writes, no PRs |
| `website/` | [youthopps.github.io](https://github.com/YouthOpps/youthopps.github.io) | Website, consuming data-source |

Submodules are pinned for workspace configuration. When executing a separately assigned project issue, fetch that project's latest `origin/main` and create the issue branch from it, without committing any changed workspace gitlink. During **skill authoring here**, they are read-only. A **separately authorized adapter-development task** can work on an issue branch *inside* the `data-pipeline` submodule and open a PR there, without updating `ai-workspace`'s gitlink or directly changing `data-source`/`website`. `data-source` never receives agent development PRs or direct commits: only the `data-pipeline` publishing automation writes to it, except for exceptional manual administrator recovery. Only a different maintainer merges that PR. Skills/workspace maintenance does not itself start any integration task.

## Shared agent workflow

This repository is the YouthOpps-specific AI workspace. Agents may use any relevant skills here. They work from this workspace but develop authorized issues inside one submodule project at a time, opening issue-linked PRs in that project's own repository. Product Owner, Architect, Developer, DevOps Engineer and QA review roles are separated when needed. PRs are merged by maintainers, who then verify acceptance, close the issue and remove obsolete branches.

All communication, documentation and commits are **in English**. Implement end-to-end fixes based on the affected code and documents together, update the relevant existing docs, keep adapter-specific guidance minimal and local, and prefer one adapter-local test file (`adapter.test.js` or `test_adapter.py`) with all relevant cases over one test file per implementation. Favor clean minimal code, concise tool output and verifiable reference links recorded in issues and relevant commits. See [AGENTS.md](AGENTS.md) and [docs/WORKFLOW.md](docs/WORKFLOW.md).

## Skills

- [Adapter](skills/adapter/SKILL.md): single skill; users may call it integration or connector.
  - [Development reference](skills/adapter/references/development.md): implementation and unmerged PR handoff.
  - [Testing reference](skills/adapter/references/testing.md): independent sandbox-first QA.

The adapter skill defines an **unsolvable** outcome where no permitted source access exists. Each adapter has its own Action and at most one local test file; a successful run writes `data-source/datas/<pretty-source-name>/data.json`, and each run records `success` or `fail`, a concise explanation and timestamps in the sibling `metadata.json`. Failures preserve last-good data. **No `data-source/catalog.json` is produced or maintained.** These are **future implementation requirements**, not changes to the current pipeline or website.

Read [AGENTS.md](AGENTS.md) before working. Additional skills may be added later. No issue or source is automatically assigned by the workspace. Skills are reusable instructions for **future, separately authorized execution**; creating or editing a skill does not authorize running it.
