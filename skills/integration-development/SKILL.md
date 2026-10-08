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
- An unsolvable/never-integrated source **must not be inserted into** `data-source/sources.json`; it may remain in research/planning manifests that are not the live registry.

## Integrated-source registry contract
On a separately authorized integration run, implement/verify `data-source/sources.json` **at the repository root** as the registry of successfully integrated sources only. This is distinct from `data-pipeline/data/sources/sources.json` (candidate/configuration manifests), `data-source/sources/<source-id>/metadata.json` (per-source metadata), and `data-source/catalog.json` (opportunity index).
- Add a source entry only after QA has confirmed authorized live retrieval of genuine validated records and successful publication; no pending, blocked, unsolvable or never-integrated sources appear.
- Use stable `source` IDs and preserve existing entries. Minimum fields per object: `source`, `status` and `last_data_received_at` (ISO-8601 UTC timestamp of the **last successful non-empty, validated real data retrieval**). Use an array of source objects; keep it sorted by `source` and pretty-printed with two-space indentation and a final newline. Optional diagnostic fields may be added with documented meanings.
- **Every scheduled/manual `fetch-<source-id>` Action run** must update its existing registry entry's `status` to `ok` on verified success or `error` on a failed/empty/invalid collection, and commit that change safely in `data-source`. A failure must not advance `last_data_received_at`, delete or overwrite the last good records, or introduce a new unintegrated entry. If the workflow cannot write a failed status, record the failure in the Action/issue and do not falsely report `ok`; repair the workflow.
- On success, set `last_data_received_at` using the actual successful retrieval time, even when returned records are unchanged. Make status/last-success updates and the existing source snapshot/catalog consistent; serialize concurrent publications and avoid races. Do not turn a failed fetch into a successful publication.
- Add targeted tests for registry initialization, first successful entry, successful re-fetch, unchanged valid data, failed/empty collection, no synthetic entries, timestamp retention and atomic/concurrent updates.

## Required developer-to-QA handoff
Provide exact changed paths, legal/technical access evidence, inventory of real source opportunities and coverage explanation, observed source-to-output mapping, run commands, tests/results, traffic counts and rate control strategy, dedup/freshness checks and remaining limitations. Never use record count alone to claim completeness.

## Verification and deployment gate
Delegate/perform independent QA using `../integration-testing/SKILL.md`; the QA role decides acceptance, not the developer. Run sandbox tests first, then—if manual checks show no errors but sandbox connectivity is the only obstacle—test in a permitted internet-connected environment. GitHub Actions live testing is an **authorized last resort** if there is no other workable route. Do not substitute Actions retries for investigation or waive legal access and rate limits.

Only after sandbox/local or authorized online collection actually produces valid source records **and QA accepts**: commit source-specific code to `data-pipeline`, trigger only the relevant `fetch-<source-id>` Action, inspect its conclusion/logs and the real output in `data-source/sources/<source-id>/` plus `catalog.json`. If production QA fails, fix, retest, recommit and rerun within safe traffic limits. Close/complete the issue only after verified publication. If upstream permission is unresolved, keep the task blocked and do not claim success.

