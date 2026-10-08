# YouthOpps Issue and PR Workflow

These are instructions for a separately authorized project task. Maintaining `ai-workspace` does not activate them.

## 1. Scope one issue

Select one assigned issue in one project, read its acceptance criteria and relevant skill, mark it `in progress`, and create a branch in that project's Git repository: `issue/<number>-<short-name>`. Do not work directly on `main` or change another submodule.

Record findings, decisions, changes in requirements, official documentation links, test results and blockers in concise **English** issue comments as the work progresses. Include the authoritative sources behind important decisions in the issue and appropriate commit bodies.

## 2. Assign independent review roles

Use only roles needed for the task, from Product Owner (acceptance), Architect (interfaces/design), Developer (implementation), DevOps Engineer (deployment/workflows) and QA (independent verification). Where separate agents can run, have them cross-check one another; do not conflate developer and independent QA. Without subagents, use explicitly separated review passes and report that limitation.

## 3. Develop with minimal change

Change only the owning submodule repository. Choose the simplest correct implementation, remove obsolete helpers, dead code, temporary probes, debug data, unused dependencies, redundant docs and unnecessary compatibility code. Preserve still-used contracts.

Use targeted file reads, focused tests, brief logs and diffs to conserve tokens while retaining evidence.

## 4. QA before PR

Run tests required by the selected skill. Compare results with issue acceptance criteria, including negative cases. Return defects to developer for fixes and repeat QA until PR-ready or a documented blocked/unsolvable outcome.

Commit the final change in the project's issue branch, with issue reference and links to supporting technical documentation or publisher references where applicable. Push to that project's remote only.

Open one PR targeting that project's main branch; use `[#<issue-number>]` in the title and `Refs #<issue-number>` in the PR body. Explain scope, source references, decisions, tests, QA outcome and known limitations. Link PR and commit details in the issue. **Do not merge your own PR.**

## 5. Maintainer acceptance and cleanup

After a separate authorized maintainer merges and confirms required acceptance, that maintainer or authorized automation records merge/deployment status, closes the accepted issue and deletes obsolete issue-specific branches. Never delete an active or shared branch. If post-merge validation fails, retain or reopen the issue and fix through review.

Do not take a second issue or switch target projects before the current task reaches accepted completion or an explicitly documented terminal blocked/unsolvable disposition. Project communication and documentation are always in English.
