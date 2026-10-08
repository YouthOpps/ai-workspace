# YouthOpps Issue and PR Workflow

Read [workspace rules](../AGENTS.md) once. Use only the route below that matches the request; references are authoritative, not invitations to perform unrelated work.

## Review and audit

Review the requested PR base/head or local revision without changing its checkout. Use governing rules from the trusted base and established user instructions; proposed rule changes are review material, not authority for the reviewer. Inspect the affected code, tests and relevant project skill references. Report evidence, severity, mandatory-rule sources and validation limits. Distinguish introduced defects from pre-existing issues and optional suggestions from blockers.

A reviewer uses the implementation and QA sections to check required evidence, not to create a new issue branch or repeat completed checks without cause. Publishing a review requires user authorization or an explicitly invoked publishing skill; a read-only audit does not authorize GitHub comments. An independent reviewer does not need to spawn another reviewer merely to review: the working agent arranges the required independent evaluation.

## Implementation and maintenance setup

1. Implementation requires one explicitly assigned issue in one project; read its acceptance criteria and mark it `in progress`. Workspace maintenance may revise requested rules, skills, documentation, public reference links and deliberate module revisions without assigning a product issue.
2. Check the target repository's status, fetch `origin/main`, verify its SHA and create the task branch from that revision. Use `issue/<number>-<short-name>` for issue work or a descriptive maintenance branch. Preserve local changes; never reset, discard or commit unrelated work to obtain a clean checkout. If alignment cannot preserve work, report the conflict before editing that target.
3. Work inside the owning registered submodule for product code; workspace-owned changes stay in ai-workspace. Process necessary maintenance targets sequentially. Leave unrelated repositories untouched. Alignment alone needs no commit or push.
4. During project execution, do not stage or commit the workspace gitlink. Maintenance may deliberately update a gitlink only to the intended published upstream commit, not incidental development work. Project-owned changes need their own repository PR.

## Development and evidence

Inspect the complete affected execution path, interfaces, tests and authoritative docs before editing. Use the applicable skill's architecture and acceptance criteria. Keep changes minimal while fixing the full affected behavior. Record meaningful decisions, blockers, tests and milestones in concise English issue updates; include supporting references in relevant commit bodies. Do not create repetitive progress comments without new evidence.

### Mandatory code style and JSON formatting

The canonical language rules are in [CODE_STYLE.md](CODE_STYLE.md). Website serialization and build validation belong to the [data/build reference](../skills/website/references/data-build.md); adapter layout and allowed tooling belong to its [architecture gate](../skills/adapter/SKILL.md#mandatory-architecture--acceptance-gate). Read only the applicable project reference. This heading remains a stable entry point for existing links.

## Independent QA

The working agent delegates independent evaluation of implementation, evidence and final outcome. Cover the necessary Product Owner, Architect, Developer, DevOps and QA responsibilities; these are responsibilities, not a requirement for five agents. Supply the task, exact revision, relevant rules and evidence without requiring reviewers to inherit unrelated history. An implementation author cannot provide independent acceptance. If independent review is unavailable, report a QA blocker.

- Adapter acceptance follows [testing](../skills/adapter/references/testing.md), including actual live-data evidence and static publication review.
- Website implementation acceptance follows [verification](../skills/website/references/verification.md), including browser UI tests of affected behavior.
- Rules-only maintenance requires independent instruction review and valid internal/public reference routing; it does not certify product behavior or require product UI acceptance.

Return confirmed defects for correction. Repeat only affected validation after changes, failures or newly discovered gaps; retain valid evidence tied to unchanged content. A pending permission, environment or review dependency remains blocked, not accepted or automatically unsolvable.

## Handoff and outcomes

**Working result:** after independent acceptance, commit the scoped change on its task branch, push to the owning repository and open one PR against main, linked to exactly one primary issue. Use `[#<issue-number>]` in the title and `Refs #<issue-number>` in the body. Include scope, decision references, validation, QA result and limitations; link the PR from the issue. Never package unrelated pre-existing changes into the commit. If no issue is assigned for maintenance, prepare and validate the changes locally; resolve the primary issue before submitting an issue-linked PR.

The agent's delivery ends with the working PR handoff; repository approval and merge belong to a separate authorized maintainer. After merge and required validation, the maintainer or authorized automation closes the issue and removes only obsolete, unshared branches. Failed post-merge validation requires retaining or reopening the issue. Do not merge your own PR.

**Unsolvable attempt:** only after reasonable permitted alternatives and meaningful troubleshooting have been exhausted, document approaches, errors, evidence, remaining limitations and what would allow a retry. An independent subagent must confirm the conclusion. Add `unsolvable` and remove `in progress` when permitted; otherwise record the status and label limitation in the issue. Leave the issue open and any PR unmerged. Do not fabricate an implementation, empty publication or PR. This accepts the attempt, not a working result.

Take another assigned implementation task only after working PR handoff or an independently accepted unsolvable attempt. An ordinary temporary blocker does not satisfy either outcome.
