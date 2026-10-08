# YouthOpps Issue and PR Workflow

These are instructions for a separately authorized project task. Maintaining `ai-workspace` does not activate them.

## 1. Scope one issue

Select one assigned issue in one project, read its acceptance criteria and relevant skill, mark it `in progress`, and create a branch in that project's Git repository: `issue/<number>-<short-name>`. Before creating the branch, run `git -C <target-submodule> fetch origin main`, inspect `git -C <target-submodule> status --short`, confirm the current `origin/main` SHA, and branch from `origin/main` (not the workspace-pinned checkout). Never discard a dirty working tree; resolve it safely first. Do not work directly on `main`, change another submodule, or stage/commit the `ai-workspace` gitlink.

Record findings, decisions, changes in requirements, official documentation links, test results and blockers in concise **English** issue comments as the work progresses. Include the authoritative sources behind important decisions in the issue and appropriate commit bodies.

## 2. Assign independent review roles

Use only roles needed for the task, from Product Owner (acceptance), Architect (interfaces/design), Developer (implementation), DevOps Engineer (deployment/workflows) and QA (independent verification). Where separate agents can run, have them cross-check one another; do not conflate developer and independent QA. Without subagents, use explicitly separated review passes and report that limitation.

## 3. Develop with minimal change

Before modifying code, inspect the **complete affected execution path**, interfaces, existing tests and relevant authoritative documents. Fix the underlying behavior across its affected components instead of making symptom-only/local patches. Change only the owning submodule repository. Choose the simplest correct implementation; reuse existing utilities/tests, and remove obsolete helpers, dead code, probes, debug data, unused dependencies/docs and needless backward-compatibility code. Preserve still-used contracts. **Update every affected section of existing project documentation in the same PR**; keep docs brief, source-specific details next to each connector, and avoid standalone documents that repeat existing guidance.

Use targeted file reads, focused tests, brief logs and diffs to conserve tokens while retaining evidence.

## 4. QA before PR

Prefer enhancing existing shared or connector tests over creating a new test for each implementation detail. Aim for **one or two focused tests per connector** covering the most important success/failure behavior, plus the existing global regression tests; add more only to address a distinct uncovered risk. Test quality and critical coverage override an arbitrary count. Run tests required by the selected skill. Compare results with issue acceptance criteria, including negative cases. Return defects to developer for fixes and repeat QA until PR-ready or a documented blocked/unsolvable outcome.

Commit the final change in the project's issue branch, with issue reference and links to supporting technical documentation or publisher references where applicable. Push to that project's remote only.

Open one PR targeting that project's main branch; use `[#<issue-number>]` in the title and `Refs #<issue-number>` in the PR body. Explain scope, source references, decisions, tests, QA outcome and known limitations. Link PR and commit details in the issue. **Do not merge your own PR.**

## 5. Maintainer acceptance and cleanup

After a separate authorized maintainer merges and confirms required acceptance, that maintainer or authorized automation records merge/deployment status, closes the accepted issue and deletes obsolete issue-specific branches. Never delete an active or shared branch. If post-merge validation fails, retain or reopen the issue and fix through review.

Do not take a second issue or switch target projects before the current task reaches accepted completion or an explicitly documented terminal blocked/unsolvable disposition. Project communication and documentation are always in English.
