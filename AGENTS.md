# YouthOpps AI Agent Workspace

This repository defines reusable, YouthOpps-specific agent skills and a shared working environment. Read this file and the relevant skill before each task. All skills are available; select only those needed.

## Repositories and work scope

- `ai-workspace`: agent instructions, skills, documentation and submodule configuration.
- `data-pipeline/`: each adapter lives in `adaptors/<pretty-source-name>/` (prefer a single `adapter.js` or `adapter.py` containing its source details and collection logic), with **at most one adapter-local test file** (`adapter.test.js` or `test_adapter.py`) and one dedicated GitHub Action per adapter.
- `data-source/`: published data repository, **not a development or PR target**. Only the authorized `data-pipeline` publication automation may commit output to `datas/<pretty-source-name>/{data,metadata}.json`; administrators may commit manually only in exceptional recovery cases. Agents must never open PRs, push branches, or directly commit to `data-source`. No `catalog.json`, aggregate index, or Actions; failures preserve last-good data.
- `website/`: static site; its `data-source` submodule is pinned.

Initialize with `git submodule update --init --recursive`.

**Workspace-maintenance mode:** change only workspace rules, skills, docs and explicitly requested setup. Do not implement project issues as part of workspace maintenance.

**Project-execution mode:** only when a project issue is explicitly assigned, work inside the owning submodule. **Fetch and verify that repository's current `origin/main` before creating the issue branch; always branch from `origin/main`, not the workspace-pinned gitlink.** Inspect and preserve any existing uncommitted changes instead of resetting them. Commit and open the PR in **that project's repository** only; never stage or commit the changed `ai-workspace` submodule pointer. Other submodules are read-only. Finish and obtain acceptance for one project's task before starting another.

## Universal agent rules

1. **English only:** all agent communication, issue/PR updates, code comments, documentation, commit messages and review notes. Use simple, clear wording without unnecessary detail.
2. **One active task:** choose one explicitly assigned issue in one project. Mark it `in progress` and keep meaningful findings, decisions, blockers, tests and milestones in the issue. Do not switch projects before that task has reached its accepted outcome.
3. **Role-based review:** use the necessary subset of Product Owner, Architect, Developer, DevOps Engineer and QA. When independent subagents are available, separate roles and require cross-review. A developer must not approve their own work as independent QA. If subagents are unavailable, use distinct review passes and disclose that limitation.
4. **Holistic, minimal changes:** inspect the relevant existing code, tests, data contracts and authoritative docs together before designing a solution. Fix the complete affected flow, not just the visible symptom. Prefer simple, maintainable code and reuse shared facilities. Remove unused files, debug artifacts, dead code, unnecessary documents/dependencies and speculative backward-compatibility branches. Preserve supported behavior unless an explicit contract change is approved.
5. **Token efficiency:** read only relevant files and diffs, limit log output and avoid repetitive scans or verbose exchanges. Never omit essential evidence or tests to save tokens.
6. **Evidence and documentation:** base choices on verifiable code, schemas and official documentation. Update **all affected sections of existing authoritative project documentation** as part of the same PR; do not leave the code and docs inconsistent. Keep docs concise and avoid repeating them across repositories. Keep source-specific details beside their adapter, using the smallest useful documentation surface. Record decision references and rationale on the issue **and in relevant commit messages/bodies**.
7. **Issue-linked branches and PRs:** each PR references exactly one primary issue and stays unmerged for an authorized maintainer. After a confirmed merge and required acceptance, the maintainer or authorized automation documents the outcome, deletes obsolete issue branches and closes the issue. The developing agent never merges their own PR or closes an unaccepted issue.
8. **Respect repository boundaries:** `data-source` accepts commits **only from `data-pipeline` publication automation** or **exceptional manual administrator operations**. Agent-initiated PRs, direct pushes or development branches in `data-source` are forbidden. This restriction also applies during multi-project work. Automated publication is not a second development task.

For the full lifecycle see [docs/WORKFLOW.md](docs/WORKFLOW.md). For source adapters, including requests described as integrations or connectors, use the single [Adapter skill](skills/adapter/SKILL.md) with its [development](skills/adapter/references/development.md) and [testing](skills/adapter/references/testing.md) references.

These rules are instructions for later authorized work; merely changing a skill does not authorize executing an issue.
