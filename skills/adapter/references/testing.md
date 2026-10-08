# Adapter Testing Reference

Read [Adapter Skill](../SKILL.md) and [workflow](../../../docs/WORKFLOW.md). This is independent QA for exactly one assigned adapter issue, not a separate skill. Use English throughout. Do not claim independent-agent review if only a single agent was available.

## Verify the source and implementation
- Verify permitted real publisher listings, pagination and representative first/last and edge records. Compare actual source titles, stable IDs, URLs, attribution, categories, countries, dates and completeness. Never approve a homepage, directory, synthetic data or unjustified inferred eligibility.
- Verify the branch started from the target project's fetched current `origin/main`, the workspace gitlink was not committed, and unrelated projects were untouched.
- Confirm `data-pipeline/adaptors/<pretty-source-name>/adapter.js` **or** `adapter.py` contains source details and implementation, preferably in **one file**. Extra files need a reason. No separate per-adapter configuration JSON.
- Confirm **one independent `fetch-<pretty-source-name>.yml` Action** invokes the exact adapter file with the selected Python/Node.js runtime and only that source.
- Inspect the full impacted validation, per-adapter publishing, metadata and downstream-consumer contracts. Require documentation updates and a clean diff. Verify there is **at most one test file inside each adapter folder** (`adapter.test.js` or `test_adapter.py`) and that its single invocation covers the necessary scenarios; use existing shared regression tests instead of multiplying adapter tests.

## Safe testing sequence
1. In the existing **sandbox**, run current pipeline-wide validation and unit tests, **the single adapter-local test entry point if present**, and a controlled real-source retrieval when possible.
2. If sandbox connectivity alone prevents real collection, use an **authorized internet-connected** environment and repeat targeted checks.
3. Only if no workable alternative exists, run the adapter in an **isolated, non-publishing GitHub Actions test**. Do not expose production write tokens or trigger privileged publishing before merge.
4. Count upstream requests: **at most 10 per target in any rolling minute**, at least 6 seconds between requests, counting retries, redirects and concurrent paths; respect stricter upstream controls.

## Validate outputs and failures
- Check generated test `data-source/datas/<pretty-source-name>/data.json` against the canonical opportunity schema and source inventory.
- Check sibling `metadata.json` for source attribution, UTC timestamps, `status: "success"` or `status: "fail"`, clear `message`, and sanitized `error` for failures. A successful retrieval advances `last_success_at`; a failure advances `last_attempt_at` and preserves previous `last_success_at` and all last-good data.
- Confirm **no `data-source/catalog.json` or root source index is created or updated**. The adapter's `metadata.json` alone reports run status, error detail and timestamps; failures preserve its previous `data.json`. No unrelated adapter's output is rewritten.
- Never open PRs or perform direct commits in `data-source`; only the `data-pipeline` publisher writes there, except for exceptional manual administrator action.
- These are temporary/test artifacts before merge. A passing PR test does **not** prove a production publication.

## Decision
- **REJECT** if source quality, permissions, completeness, validation, failure behavior, request pacing, workflow routing, docs or code scope are wrong. Give reproducible evidence and return to the developer.
- **BLOCKED** if a plausible official access/test route remains pending. Explain the blocker.
- **UNSOLVABLE** if reasonable lawful collection routes are exhausted: require detailed issue evidence and the `unsolvable` mark, without an empty publication.
- **ACCEPT (PR-ready)** only after successful real-data checks, safe traffic, correct failure handling, clean scope and documented results. Approve an unmerged issue-linked PR, not a merge/deployment.

Record concise issue/PR evidence: revision, commands, source sample links, actual counts/coverage, failures, request limits, per-adapter data/metadata results and decision. Another maintainer handles merge and post-merge acceptance.
