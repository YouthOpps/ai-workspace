# YouthOpps AI Agent Workspace

Shared rules for work in this workspace. Read the applicable skill and only the references required for the task. Reuse instructions already read in this session unless they changed.

## Provider-independent scope

These rules and all project skills apply to every AI agent and AI-assisted developer, including Claude, Codex, Gemini and other providers, regardless of model, editor or execution environment. `AGENTS.md` and the Markdown skill files are authoritative project instructions; provider-specific entry files only point here and must not duplicate or override the rules.

Use equivalent available capabilities for file access, Git, PR APIs, shell execution, browser testing and independent review. Named tools, `$skill-name` invocation syntax and `agents/openai.yaml` UI metadata are optional host integrations, not provider requirements. Without native skill discovery, explicitly read the relevant `skills/<name>/SKILL.md` and its required references. Missing optional integrations do not block work; missing required evidence or permissions does, and must never be reported as a pass. Tool substitutions do not expand authorization or bypass host restrictions.

Throughout these rules, an independent subagent may be a native delegated agent or a separately assigned reviewer agent/session from any provider. It must independently examine the revision and evidence and must not be the implementation author performing another self-review. If neither route is available, report the review dependency rather than weakening acceptance.

## Mandatory AI workspace gate

Development must use [ai-workspace](https://github.com/YouthOpps/ai-workspace) and its registered submodules; standalone project development is prohibited. Reuse an existing checkout or clone it and run `git submodule update --init --recursive`. Skills and workspace rules are maintained here. If required instructions or the workspace are unavailable, stop development and report the blocker.

## Repositories and work scope

| Target | Authority and boundary |
|---|---|
| `ai-workspace` | Shared rules, skills, docs and deliberate submodule revisions |
| `data-pipeline/` | [Adapter skill](skills/adapter/SKILL.md); standalone adapter and test, with documentation in the adapter's own README |
| `website/` | [Website skill](skills/website/SKILL.md); static site with pinned data-source input |
| PR review | [PR Review skill](skills/pr-review/SKILL.md); evidence-based review and authorized publication, combined with the affected project's skill |
| `data-source/`, including website's nested checkout | Publication-only: authorized pipeline automation or exceptional manual administrator recovery. No agent development, branches, direct commits/pushes or PRs. No aggregate catalog or Actions. Correct data through data-pipeline. |

Choose the task mode before acting:

- **Review/audit:** inspect the requested revision and applicable rules. Do not align branches, mark an issue in progress or start implementation merely to review. Read the workflow's review section and relevant project acceptance criteria.
- **Implementation:** one explicitly assigned issue in its owning submodule. Follow [workflow](docs/WORKFLOW.md) for branch setup, independent QA and PR handoff.
- **Workspace maintenance:** edit requested skills/rules and necessary public reference links. Follow the workflow's maintenance route. This does not assign a product issue or authorize production execution.

## Universal agent rules

- Use English for project communication, issue/PR updates, documentation, code comments, commits and reviews. Keep wording concise and factual.
- Preserve existing user work and supported contracts. Inspect the complete affected flow, fix the underlying problem, and remove obsolete code or artifacts only within the assigned scope.
- Apply [code style](docs/CODE_STYLE.md) to authored code and code reviews. Project architecture and public contracts take precedence over generic style advice.
- Update every affected section of authoritative documentation with the change. Put source-specific adapter explanations in its folder's `README.md`; adapter work must leave the data-pipeline root `README.md` unchanged. Record decision evidence and references in the issue and relevant commit bodies.
- Independent subagent evaluation is required for delivery, including rules maintenance and an unsolvable conclusion. The author cannot independently accept their own work; internal QA is separate from repository approval. See the workflow for responsibilities and outcomes.
- Keep reads, tool output and reviewer context proportional to the task. Load specific sections, summarize repetitive logs and validate large datasets programmatically without discarding coverage. Recheck changed evidence rather than repeating unchanged scans.

The project skills own domain acceptance rules; the workflow owns lifecycle rules. The website skill's current requirements supersede conflicting older website conventions. Editing a skill does not authorize executing it. Do not merge your own PR or develop directly on `main`.
