# Adapter collection and publication contract

Read for collection, validation, pacing, metadata, publication or corresponding review. The architecture is defined in the parent skill; lifecycle is defined in the workspace workflow.

## Collection

- Use permitted official publisher access and genuine opportunities; no synthetic records or unsupported eligibility inference. Honor terms, robots, approved access methods and stricter publisher limits.
- Each adapter may start at most 10 upstream requests in any rolling 60 seconds, at least 6 seconds apart across endpoints, retries, redirects, pagination and concurrent paths. Coordinate or serialize overlapping test/production runs of that adapter under the same allowance. Distinct adapters need no shared allowance unless the publisher imposes one. Honor backoff.
- Validate nonempty records, source identity, stable IDs, duplicate IDs, URLs, dates, attribution and classification inside the implementation. Preserve existing public field names and envelopes; do not introduce a separate/shared schema file.

## Publication

The production Action publishes only its source's `data-source/datas/<pretty-source-name>/{data,metadata}.json`. Use atomic, source-scoped, serialized or conflict-safe commits. Do not rewrite another source or create an aggregate `catalog.json`, `sources.json` or index.

| Prior publication | Current outcome | Required effect |
|---|---|---|
| None | Valid nonempty collection successfully published | Atomically create data and metadata together; status `success` |
| None | Any failure | Create no folder, data or metadata; report sanitized failure in Action logs and issue evidence |
| Successful publication exists | New successful publication | Replace data with validated records and update success metadata together |
| Successful publication exists | Fetch/parse/validate/publish failure | Preserve last-good data and success timestamp; record failure metadata when possible |

Metadata contains source identity/attribution, `status` (`success` or `fail`), concise `message`, UTC ISO-8601 `last_attempt_at` and `last_success_at`, and a sanitized actionable `error` plus failure stage when known. Advance `last_success_at` only when valid nonempty retrieval is successfully published. Failure reporting must not erase prior source information or claim durable status was saved if metadata publication failed.

After first success, source metadata is the sole durable run-status record. Before first success, blocked or unsolvable sources have no published folder. Production publication begins after maintainer merge. Tests never publish or receive publication credentials; a collection test and static code review do not prove production publication.
