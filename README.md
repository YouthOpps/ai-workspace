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

Submodules are pinned as **read-only project references for workspace configuration**. Update their pointers only when explicitly requested as a workspace-maintenance task. Developing issues, implementing integrations, changing production code, publishing data, and running GitHub Actions are **out of scope for work on this repository**.

## Skills

- [Integration development](skills/integration-development/SKILL.md): one-source developer process with QA handoff.
- [Integration testing](skills/integration-testing/SKILL.md): independent completeness and safety gate, sandbox-first; online environment second; GitHub Actions last resort.

Read [AGENTS.md](AGENTS.md) before working. Additional skills may be added later. No issue or source is automatically assigned by the workspace. Skills are reusable instructions for **future, separately authorized execution**; creating or editing a skill does not authorize running it.
