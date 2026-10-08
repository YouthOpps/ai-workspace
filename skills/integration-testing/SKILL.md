---
name: integration-testing
description: Act as independent QA gatekeeper for one YouthOpps source integration; test completeness, correctness and safe access before production release.
---

# Opportunity Integration QA — Independent Test Agent

## Scope and authority
This file **defines a reusable QA process only**. While maintaining `ai-workspace`, do not execute QA against source issues, change submodules, trigger Actions or publish data. Activate only for an issue explicitly assigned in a **separate integration-development task**. Review exactly that one `in progress` issue. Never approve an integration simply because tests pass or one URL returns HTTP 200. Do not select another issue before this one is accepted or explicitly blocked. Return concrete, reproducible defects to the Integration Engineer and repeat until resolved.

## Gate 1 — Source authenticity and coverage
- Check current official source, allowed collection method and observed inventory of all **relevant accessible published opportunities**, across pagination, categories and date windows. State coverage evidence and its limits; never guess total expected count.
- Compare representative source listings against extracted records, including first and last pages and edge cases if available.
- Reject generic FAQs, search directories, invented records, invalid URLs, stale duplication, non-opportunity content, lost opportunity pages, missing original attribution and unsupported deadlines, destinations or eligibility assertions.
- Validate every record against canonical schema; verify stable IDs, deduplication, category/country accuracy, timestamps and freshness behavior, JSON readability, deterministic output where appropriate, and safe failure handling.
- An inaccessible or disallowed publisher means **BLOCKED**, not `PASS`. Do not bypass restrictions or relabel the issue as complete.

## Gate 2 — Safe network behavior
- Count every upstream HTTP request, including retries, redirects and linked-page fetches. Rate limit each target to **no more than 10 requests in any rolling 60 seconds**, plus minimum 6 seconds between requests; honor tighter source limits, `Retry-After` and throttling errors.
- Inspect concurrency, timeout, bounded retries, failures and zero-result handling. A successful response to aggressive crawling is still a QA failure.

## Gate 3 — Test environment ladder (explicit authorization)
1. Run `npm ci --ignore-scripts`, `npm run validate`, `npm test`, plus source-specific fixtures and collection in the **existing sandbox**. Check that actual valid data can be collected; fixtures alone do not prove a live integration.
2. If manual review shows no evident code/data errors but the sandbox cannot reach the internet/source, use another **authorized, internet-connected environment** to run the same targeted tests and controlled real collection. Distinguish network restrictions from extractor failures.
3. **Only if no workable alternative remains, GitHub Actions may be used to test in the live runner**. This is expressly permitted by the project owner. Trigger only the one source's Action; avoid triggering unrelated jobs or production publication with unverified data. Respect the traffic cap in every environment and do not repeatedly trigger jobs to circumvent it.
4. Confirm real results in both `data-source/sources/<source-id>/metadata.json`, `opportunities.json`, and unified `catalog.json` after controlled publication. Confirm pipeline status, run logs, data accuracy and no unrelated data loss.

## Per-connector publication and unresolved-source verification
- Confirm that **each integrated adapter has one independent `fetch-<connector-id>` GitHub Action** and it executes only that source adapter.
- For the tested connector verify `data-source/sources/<connector-id>/opportunities.json` contains validated real source records and `data-source/sources/<connector-id>/metadata.json` contains accurate publisher metadata, `status`, `last_attempt_at`, `last_success_at` and collection count/provenance.
- Verify every Action invocation updates this connector's `metadata.json` status. Successful retrieval advances `last_success_at` even if contents are unchanged; a failed or empty fetch records `status: "error"` but preserves the last successful retrieval time and all valid prior opportunity records.
- Check the unified `data-source/catalog.json` after successful publication and confirm no unrelated connector files change. Verify safe serialized commits under concurrent publishing.
- **There must be no requirement to write root-level `data-source/sources.json`**; status/freshness are stored per connector under its own source folder.
- When no authorized acquisition route exists after reasonable attempts, require a detailed issue comment and an **unsolvable** outcome. Do not publish an empty folder or fabricated records.

## QA decision
- **REJECT**: any reproducible extraction, schema, coverage, safety or quality defect; provide exact evidence and a developer correction request.
- **BLOCKED**: some viable option or missing permission is still being investigated; document attempts and preconditions, keep existing published data safe.
- **UNSOLVABLE**: reasonable lawful collection routes have been exhausted and no workable route exists; post detailed evidence to the issue, mark it unsolvable, leave it out of the live source registry and stop work.
- **ACCEPT**: authorized access, demonstrated coverage, source-backed records, tests and real collection pass, bounded traffic proven. Then permit developer commit and targeted Action run, followed by a second post-deployment check.

Record in the issue: tested revision/SHA, commands, environment, sample source links, record counts, missed items, rate evidence, Action URL/status (if used), output paths, QA decision and unresolved risks. No empty, synthetic or homepage-only publication counts as acceptance.
