---
name: integration-development
description: Implement exactly one YouthOpps opportunity-source integration through evidence-based source access, developer work, independent QA, local-first tests, and gated production validation.
---

# Opportunity Source Integration — Developer Agent

## Activation and task lock
This file **defines a reusable process only**. While maintaining `ai-workspace`, do not execute it, modify submodule code, touch issues, trigger Actions or publish data. Activate this skill only during a **separate, explicitly authorized source-integration task** in an appropriate working environment.

1. Work on **one** specifically assigned GitHub issue; do not choose or modify others.
2. On activation, confirm that the assigned issue is open and labeled `in progress`. If needed, apply that label only as part of the separately authorized task. Do not silently switch tasks.
3. Treat the issue's acceptance criteria as the contract. Record source ID, publisher, official listing location, expected record types, and approved access method.
4. Make all collector code changes in `data-pipeline/`. Do not edit `website/` or handwrite the published `data-source/` JSON as a substitute for working collection.

## Developer role — Integration Engineer
1. Inspect README, manifests (`data/sources/sources.json`, `source-registry.json`), `scripts/collect.js`, adapters, tests, schema and existing per-source workflow conventions before changing code.
2. Verify the publisher's actual current site, source terms/robots and any API, feed, sitemap, paginated listings or approved alternative endpoint. An invalid/unavailable robots policy is **not** permission to scrape; resolve permission with the publisher or use an independently authorized official interface. Do not spoof identities, bypass CAPTCHAs, authenticate without authorization or work around access controls.
3. Capture real individual opportunities rather than generic pages, FAQ entries, directory landing pages, or fabricated records. Preserve official title, canonical URL, source attribution, category, countries and dates only where supported by evidence. Use stable record IDs; preserve first-seen history; deduplicate; keep missing eligibility/deadlines unknown, not inferred.
4. Reuse an existing reviewed adapter where possible. If a new one is necessary, register it explicitly, update manifest validation and implement focused positive, negative and fixture tests. Do not weaken shared validators.
5. All HTTP entry points—including retries, redirects, nested link fetches, diagnostics and concurrent jobs—must use one origin-aware rate controller. Maximum **10 requests per rolling 60 seconds to the same target**, with at least 6 seconds between requests; honor `Retry-After`, 429, 503 and stricter server rules; use bounded exponential backoff, jitter and limited concurrency. Never hammer the upstream publisher. Avoid requests when fixtures suffice.
6. Emit schema-valid, 2-space-indented JSON with trailing newline via the existing publishing scripts. Preserve an existing valid snapshot if collection is empty, restricted or failed.
7. No speculative completion: repeatedly improve implementation based on QA rejection until objective acceptance is met or report an unresolved, documented block.

## Unsolvable integration (terminal outcome)
If documented investigation finds **no legally permitted and technically workable route to retrieve real opportunity records** (official API/feed, approved public listing, alternate official endpoint or publisher permission), do not fabricate records, enable a dead integration, or keep retrying indefinitely.
- Exhaust reasonable distinct options once, with evidence, bounded attempts and publisher-safe traffic. Do not interpret an inaccessible sandbox alone as proof of impossibility; follow the environment ladder in the QA skill.
- Add a detailed comment to the assigned GitHub issue covering tested URLs/methods, permission/robots findings, responses/errors, environments, dates, relevant logs, attempted remedies and why each route failed, plus a clear prerequisite that would unblock the integration. Do not disclose secrets.
- Mark the issue **unsolvable** using the repository's existing label/status convention (e.g. `unsolvable`; create a label only if separately authorized). Leave the issue open unless the project's explicit closure policy says otherwise. Stop work on it and report this outcome. Do not mark it successfully integrated or publish a placeholder.
- An unsolvable/never-integrated source **must not have published files created** under `data-source/sources/<connector-id>/`; it may remain in research/planning manifests.

## Independent Action and per-connector publication contract
- Every successfully integrated connector has **one independent** `data-pipeline/.github/workflows/fetch-<connector-id>.yml` GitHub Action, which invokes **only its matching adapter**. Shared publishing concurrency may serialize writes to prevent conflicts; no unrelated connector is fetched by that Action.
- The adapter fetches real, validated publisher opportunities and publishes its output to **`data-source/sources/<connector-id>/opportunities.json`**. Use the existing canonical schema and pretty-printed JSON with a trailing newline.
- The same connector has **`data-source/sources/<connector-id>/metadata.json`**, containing publisher/source metadata, the latest run `status`, `last_attempt_at` and **`last_success_at`** (time of the most recent successful retrieval of real validated data), using UTC ISO-8601 timestamps. The actual published record count and any supported provenance fields should remain accurate.
- On every Action run, update that connector's `metadata.json`: set `status: "ok"` and advance `last_success_at` only after successful real non-empty validated collection; on collection error set `status: "error"` and advance `last_attempt_at`, while **preserving** `last_success_at` and existing valid opportunities. Ensure the failure-status update can run even when fetch fails; report a failed metadata write rather than claiming success.
- Successful source publication should rebuild `data-source/catalog.json` using the existing shared publisher, without hand-editing the catalog or losing other sources. Updates to the targeted source's opportunities, metadata and unified catalog should be consistent; serialize shared data-source commits to avoid lost updates.
- **Do not create, update or rely on a root-level `data-source/sources.json` registry.** Its previously proposed status-index behavior is superseded. The only per-connector source status and last successful data retrieval record is `sources/<connector-id>/metadata.json`.
- Never create `sources/<connector-id>/` output for a candidate, blocked or unsolvable connector that has not successfully integrated. The pipeline's `data/sources/sources.json` remains the configuration/research manifest, not a published status registry.
- Test isolated Action execution, valid records, metadata status transitions, successful refresh with unchanged content, failed/empty response without data loss, safe retry/rate limiting and absence of unrelated source changes.

## Required developer-to-QA handoff
Provide exact changed paths, legal/technical access evidence, inventory of real source opportunities and coverage explanation, observed source-to-output mapping, run commands, tests/results, traffic counts and rate control strategy, dedup/freshness checks and remaining limitations. Never use record count alone to claim completeness.

## Verification and deployment gate
Delegate/perform independent QA using `../integration-testing/SKILL.md`; the QA role decides acceptance, not the developer. Run sandbox tests first, then—if manual checks show no errors but sandbox connectivity is the only obstacle—test in a permitted internet-connected environment. GitHub Actions live testing is an **authorized last resort** if there is no other workable route. Do not substitute Actions retries for investigation or waive legal access and rate limits.

Only after sandbox/local or authorized online collection actually produces valid source records **and QA accepts**: commit source-specific code to `data-pipeline`, trigger only the relevant `fetch-<source-id>` Action, inspect its conclusion/logs and the real output in `data-source/sources/<source-id>/` plus `catalog.json`. If production QA fails, fix, retest, recommit and rerun within safe traffic limits. Close/complete the issue only after verified publication. If upstream permission is pending, keep the task blocked; if all permitted acquisition routes have been exhausted, document and mark the issue unsolvable. Never claim success without validated records.

