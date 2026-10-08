# Adapter Development Reference

Read [Adapter Skill](../SKILL.md) and the workspace rules. Execute only for one assigned data-pipeline issue, in English.

## Source and branch
- Mark the assigned issue `in progress`; fetch and verify current `data-pipeline/origin/main`, check a clean working tree, then create `issue/<number>-<pretty-source-name>` from that commit. Do not change or commit workspace gitlinks.
- Use a single stable lowercase kebab-case source slug for both project paths. Review the complete affected dispatch, schemas, validation, catalog and publishing flow before coding; update affected existing documentation, avoid superficial fixes.
- Research the official publisher, genuine opportunity inventory, terms/robots, approved access methods, pagination and provenance. Unknown access rights never justify bypassing restrictions.
- Choose **Node.js or Python** per source based on suitability and minimal dependencies. Prefer one self-contained `data-pipeline/adaptors/<pretty-source-name>/adapter.js` or `adapter.py`. Keep publisher URLs, source metadata, parsing rules and code there. Extra files only when genuinely necessary. Never require separate adapter configuration JSON. Central shared validation/publishing helpers are allowed.
- Each adapter owns one independent `data-pipeline/.github/workflows/fetch-<pretty-source-name>.yml` which calls that adapter file/class using the appropriate runtime. One Action does not collect other adapters.

## Output contract
- On successful verified collection, the Action publishes `data-source/datas/<pretty-source-name>/data.json` containing genuine schema-valid opportunities; it records a corresponding `metadata.json`.
- `metadata.json` must record source identity and attribution, `status` (`success` or `fail`), a concise outcome `message`, `last_attempt_at` and `last_success_at` in UTC ISO-8601; failure includes a sanitized actionable `error` and failure stage when known. `last_success_at` changes **only** after a successful nonempty valid retrieval. On failed fetch/parse/validate/publish, update status and explanation while preserving `last_success_at`, last-good `data.json`, and prior source data.
- Keep the existing `data-source/catalog.json` source entry aligned with `metadata.json` status, explanation and timestamps on **success and failure**, without losing previously valid opportunity rows. Validate output and publish consistently using serialized or conflict-safe commits. If durable status publication itself fails, report it rather than claiming success.
- An unintegrated, blocked or unsolvable adapter must not create `data-source/datas/<pretty-source-name>/` as a published source. No root `data-source/sources.json` index.
- Request limit: maximum **10 per target in any rolling 60 seconds** and minimum 6-second interval; include retries, redirects and pagination, honor stricter limits and backoff.

## Implementation and QA
- Prefer **one or two focused adapter-specific tests**, extending existing shared tests for common behavior. Add more tests only for distinct material risks; verify actual data, deduplication, correctness, negative cases, failure preservation and catalog consistency.
- Keep source-specific notes beside the adapter in the same source file when possible; update all relevant existing docs. Do not leave temporary probes, unused scripts, dead code, duplicate documentation, speculative backwards compatibility or unnecessary dependencies.
- Independent QA follows [Testing](testing.md): sandbox first, then an authorized networked environment, then isolated non-publishing Actions as last resort. Fix and resubmit rejected results. Never use production publication to test unmerged changes.

## Issue result and handoff
- If no permitted working route for real data exists after bounded documented efforts, leave a detailed issue comment with endpoints, permissions, observed failures, dates and unblock requirements. Mark it `unsolvable`, remove `in progress`, leave it open for reconsideration, and do not create a fake adapter/Action or published data.
- After QA approves, commit **only in data-pipeline** issue branch, push and open one issue-linked PR targeting data-pipeline main. Include documented evidence and chosen runtime, record the PR on the issue, and **do not merge**. Another maintainer owns merge, post-merge validation, issue closure and obsolete branch removal. Do not commit `data-source` or `website` changes.
