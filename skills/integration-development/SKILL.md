---
name: integration-development
description: Implement exactly one YouthOpps opportunity-source integration through evidence-based source access, developer work, independent QA, local-first tests, and gated production validation.
---

# Opportunity Source Integration — Developer Agent

## Mandatory task lock
1. Work on **one** explicitly assigned GitHub issue; do not select or modify others. For the initial run, the designated task is **YouthOpps/data-pipeline#11 (be-ares)**.
2. Confirm that the issue is open and labeled `in progress`. If not labeled, apply that label before starting; if another task is assigned, never switch silently.
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

## Required developer-to-QA handoff
Provide exact changed paths, legal/technical access evidence, inventory of real source opportunities and coverage explanation, observed source-to-output mapping, run commands, tests/results, traffic counts and rate control strategy, dedup/freshness checks and remaining limitations. Never use record count alone to claim completeness.

## Verification and deployment gate
Delegate/perform independent QA using `../integration-testing/SKILL.md`; the QA role decides acceptance, not the developer. Run sandbox tests first, then—if manual checks show no errors but sandbox connectivity is the only obstacle—test in a permitted internet-connected environment. GitHub Actions live testing is an **authorized last resort** if there is no other workable route. Do not substitute Actions retries for investigation or waive legal access and rate limits.

Only after sandbox/local or authorized online collection actually produces valid source records **and QA accepts**: commit source-specific code to `data-pipeline`, trigger only the relevant `fetch-<source-id>` Action, inspect its conclusion/logs and the real output in `data-source/sources/<source-id>/` plus `catalog.json`. If production QA fails, fix, retest, recommit and rerun within safe traffic limits. Close/complete the issue only after verified publication. If upstream permission is unresolved, keep the task blocked and do not claim success.

## Initial assignment: #11
`be-ares` has a documented access limitation and is disabled in its manifest. Confirm official ARES opportunity listings and approved access before enabling or publishing it. A landing page, manually invented scholarship or unauthorized fetch does not satisfy #11.
