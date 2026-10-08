# YouthOpps AI Agent Workspace

This repository defines reusable, YouthOpps-specific agent skills and a shared working environment. Read this file and the relevant skill before each task. All skills are available; select only those needed.

## Repositories and work scope

- `ai-workspace`: agent instructions, skills, documentation and submodule configuration.
- `data-pipeline/`: integrations, adapters, tests and independent fetch Actions.
- `data-source/`: published opportunity data, per-connector metadata and catalog; no Actions.
- `website/`: static site; its `data-source` submodule is pinned.

Initialize with `git submodule update --init --recursive`.

**Workspace-maintenance mode:** change only workspace rules, skills, docs and explicitly requested setup. Do not implement project issues as part of workspace maintenance.

**Project-execution mode:** only when a project issue is explicitly assigned, develop inside the relevant submodule's own issue branch; commit and open its PR in **that project's repository**. Do not update the `ai-workspace` submodule pointer. Other submodules may be consulted read-only. Do not modify multiple project repositories within one task: finish one project and obtain acceptance before starting another.

## Universal agent rules

1. **English only:** all agent communication, issue/PR updates, code comments, documentation, commit messages and review notes. Use simple, clear wording without unnecessary detail.
2. **One active task:** choose one explicitly assigned issue in one project. Mark it `in progress` and keep meaningful findings, decisions, blockers, tests and milestones in the issue. Do not switch projects before that task has reached its accepted outcome.
3. **Role-based review:** use the necessary subset of Product Owner, Architect, Developer, DevOps Engineer and QA. When independent subagents are available, separate roles and require cross-review. A developer must not approve their own work as independent QA. If subagents are unavailable, use distinct review passes and disclose that limitation.
4. **Minimal clean changes:** prefer simple, maintainable code. Remove unused files, debug artifacts, dead code, unnecessary documentation, dependencies and obsolete compatibility workarounds. Do not delete still-used functionality.
5. **Token efficiency:** read only relevant files and diffs, limit log output and avoid repetitive scans or verbose exchanges. Never omit essential evidence or tests to save tokens.
6. **Evidence and references:** base choices on verifiable code, specs and official documentation. Record cited references and rationale on the issue **and in relevant commit messages/bodies**. Do not invent information.
7. **Issue-linked branches and PRs:** each PR references exactly one primary issue and stays unmerged for an authorized maintainer. After a confirmed merge and required acceptance, the maintainer or authorized automation documents the outcome, deletes obsolete issue branches and closes the issue. The developing agent never merges their own PR or closes an unaccepted issue.
8. **Respect repository boundaries:** automated, post-merge collection from `data-pipeline` into `data-source` is permitted by the platform's runtime contract; it does not justify cross-repository development commits.

For the full lifecycle see [docs/WORKFLOW.md](docs/WORKFLOW.md). For opportunity connectors see [Integration Development](skills/integration-development/SKILL.md) and [Integration Testing](skills/integration-testing/SKILL.md).

These rules are instructions for later authorized work; merely changing a skill does not authorize executing an issue.
