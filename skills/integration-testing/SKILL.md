---
name: integration-testing
description: Independently QA a single Node.js or Python connector and its clean, source-scoped data-pipeline PR, without merging or prematurely publishing production data.
---

# Opportunity Integration QA — Independent Test Agent

## Scope and authority
Follow [workspace rules](../../AGENTS.md) and [issue workflow](../../docs/WORKFLOW.md). Use only necessary independently reviewing roles (Product Owner, Architect, Developer, DevOps Engineer and QA), keep findings concise and grounded in authoritative references, and report significant findings in the issue and relevant commits. **All communication and documentation must be in English.** If independent agents cannot be used, state that explicitly instead of claiming independent-agent review.

This file **defines a reusable QA process only**. While maintaining `ai-workspace`, do not execute QA against source issues, change submodules, trigger Actions or publish data. Activate only for an issue explicitly assigned in a **separate integration-development task**. Review exactly that one `in progress` issue. Never approve an integration simply because tests pass or one URL returns HTTP 200. Do not select another issue before this one is accepted or explicitly blocked. Return concrete, reproducible defects to the Integration Engineer and repeat until resolved.

## Gate 1 — Source authenticity and coverage
- Check current official source, allowed collection method and observed inventory of all **relevant accessible published opportunities**, across pagination, categories and date windows. State coverage evidence and its limits; never guess total expected count.
- Compare representative source listings against extracted records, including first and last pages and edge cases if available.
- Reject generic FAQs, search directories, invented records, invalid URLs, stale duplication, non-opportunity content, lost opportunity pages, missing original attribution and unsupported deadlines, destinations or eligibility assertions.
- Validate every record against canonical schema; verify stable IDs, deduplication, category/country accuracy, timestamps and freshness behavior, JSON readability, deterministic output where appropriate, and safe failure handling.
- An inaccessible or disallowed publisher means **BLOCKED**, not `PASS`. Do not bypass restrictions or relabel the issue as complete.

## Holistic review, documentation and lean tests
- Before evaluating the change, verify the issue branch was created from the latest fetched target repository `origin/main`, with the workspace's pinned submodule gitlink unchanged and no unrelated local changes lost.
- Review the entire affected path (adapter, manifest, dispatcher, validator, publication, catalog, workflow and existing documentation). Reject isolated symptom patches, duplicated logic and undocumented contract changes.
- Check that every impacted section of the existing authoritative project docs is updated, with **minimal connector-local documentation** and no unnecessary duplicate documents.
- Prefer extending shared tests and aim for **one or two focused connector-specific tests** covering the critical success and failure behavior. Additional tests must be justified by distinct uncovered risks; never compromise required verification to meet a numeric target.

## Runtime and change-scope review
- Verify the engineer evaluated Node.js versus Python and chose an appropriate primary runtime for the connector. Check its one-to-one Action setup (`setup-node` or `setup-python`), pinned dependencies, tests and explicit integration with the existing canonical schema/publishing interface.
- Reject orphan files, temporary probes, debug output, dead branches, speculative backwards-compatibility code, unused dependencies, irrelevant documentation, duplicate adapters and unrelated changes; protect still-used shared code from accidental deletion.
- Confirm **only `data-pipeline/` changes are committed and proposed in the integration PR**. `data-source` and `website` remain untouched in the development branch; no `ai-workspace` gitlink update is committed.

## Gate 2 — Safe network behavior
- Count every upstream HTTP request, including retries, redirects and linked-page fetches. Rate limit each target to **no more than 10 requests in any rolling 60 seconds**, plus minimum 6 seconds between requests; honor tighter source limits, `Retry-After` and throttling errors.
- Inspect concurrency, timeout, bounded retries, failures and zero-result handling. A successful response to aggressive crawling is still a QA failure.

## Gate 3 — Test environment ladder (explicit authorization)
1. In the **existing sandbox**, run the pipeline-wide Node validation/tests (`npm ci --ignore-scripts`, `npm run validate`, `npm test`) and the **chosen connector runtime's tests**: Node's source-specific tests or Python's pinned-dependency installation and Python unit tests/pytest as appropriate. Test source-specific fixtures and controlled permitted real collection. Check that valid real data can be collected; fixtures alone do not prove a live integration.
2. If manual review shows no evident code/data errors but the sandbox cannot reach the internet/source, use another **authorized, internet-connected environment** to run the same targeted tests and controlled real collection. Distinguish network restrictions from extractor failures.
3. **Only if no workable alternative remains, GitHub Actions may be used as a last-resort testing runner**, as permitted by the project owner. **Before the PR is merged, use an isolated, non-publishing test** of the targeted connector (no writes to `data-source` and no production data-source token); never trigger the production-publishing flow for an unmerged branch. Respect the traffic cap and do not repeatedly trigger jobs to circumvent it.
4. Before PR handoff, validate the adapter's **temporary/test output** against `data-source/sources/<source-id>/metadata.json`, `opportunities.json`, and `catalog.json` contract, including success/failure behavior and no unrelated data loss. Live publication is **not** part of PR acceptance; verify actual `data-source` results only in a separately authorized **post-merge** task.

## Per-connector publication and unresolved-source verification
- Confirm that **each integrated adapter has one independent `fetch-<connector-id>` GitHub Action** and it executes only that source adapter.
- For the tested connector verify `data-source/sources/<connector-id>/opportunities.json` contains validated real source records and `data-source/sources/<connector-id>/metadata.json` contains accurate publisher metadata, `status`, `last_attempt_at`, `last_success_at` and collection count/provenance.
- Verify every Action invocation updates this connector's `metadata.json` status. Successful retrieval advances `last_success_at` even if contents are unchanged; a failed or empty fetch records `status: "error"`, sanitized actionable `error` detail and `last_attempt_at`, but preserves `last_success_at`, `last_checked_at`, prior record count and all valid opportunity records. A failed publication must never be recorded as a successful fetch/publication.
- Check that `data-source/catalog.json` contains the same status, error and timestamps in its matching `sources[]` entry after **both successful and failed** runs, retaining last-good opportunity rows on failure. Validate single consistent/serialized commits and ensure other connectors remain untouched.
- **There must be no requirement to write root-level `data-source/sources.json`**; status/freshness are stored per connector under its own source folder.
- When no authorized acquisition route exists after reasonable attempts, require a detailed issue comment and an **unsolvable** outcome. Do not publish an empty folder or fabricated records.

## QA decision
- **REJECT**: any reproducible extraction, schema, coverage, safety or quality defect; provide exact evidence and a developer correction request.
- **BLOCKED**: some viable option or missing permission is still being investigated; document attempts and preconditions, keep existing published data safe.
- **UNSOLVABLE**: reasonable lawful collection routes have been exhausted and no workable route exists; post detailed evidence to the issue, mark it unsolvable, leave it out of the live source registry and stop work.
- **ACCEPT (PR-ready)**: authorized access, demonstrated coverage, source-backed records, runtime-specific tests and real collection pass, bounded traffic proven, clean diff and independent Action verified. Permit a **data-pipeline-only commit and issue-linked PR**, not merge or production publication. Another maintainer will merge; any post-merge production QA is separately authorized.

Record in the issue/PR: tested revision/SHA, chosen runtime, commands, environment, sample source links, record counts, missed items, rate evidence, isolated Action test URL/status (if used), expected output paths, clean-diff review, QA decision and unresolved risks. Confirm the PR is **open and unmerged** and no other repository was committed. After an authorized maintainer merges and accepts the changes, the maintainer or authorized automation closes the issue and deletes obsolete issue branches, recording that outcome. No empty, synthetic or homepage-only collection counts as acceptance.
