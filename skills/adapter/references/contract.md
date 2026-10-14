# Adapter collection and publication contract

Read for collection, validation, pacing, metadata, publication or corresponding review. The architecture is defined in the parent skill; lifecycle is defined in the workspace workflow.

## Collection

- Use permitted official publisher access and genuine opportunities; no synthetic records or unsupported eligibility inference. Honor terms, robots, approved access methods and stricter publisher limits.
- Each adapter may start at most 10 upstream requests in any rolling 60 seconds, at least 6 seconds apart across endpoints, retries, redirects, pagination and concurrent paths. Coordinate or serialize overlapping test/production runs of that adapter under the same allowance. Distinct adapters need no shared allowance unless the publisher imposes one. Honor backoff.
- Validate nonempty records, source identity, stable IDs, duplicate IDs, URLs, dates, attribution and classification inside the implementation. Preserve existing public field names and envelopes; do not introduce a separate/shared schema file.
- Final record IDs must match the current [website consumer](https://github.com/YouthOpps/youthopps.github.io/blob/main/scripts/data.mjs) grammar `^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$`. Use stable globally unique identities, normally the source slug followed by a stable native identifier or deterministic digest. Reject duplicates case-insensitively; colons, underscores, whitespace and other separators are invalid.
- Validate final IDs and all records after every native-ID assignment or override, before returning the complete collection and before publication. Earlier validation of an intermediate/generated ID does not validate the final native ID. Preserve identity across repeated collection; do not derive it from record order or mutable titles.

## Publication

The production Action publishes only its source's `data-source/datas/<pretty-source-name>/{data,metadata}.json`. Use atomic, source-scoped, serialized or conflict-safe commits. Do not rewrite another source or create an aggregate `catalog.json`, `sources.json` or index.

For an explicitly scoped ID migration, legacy-ID acceptance may be an opt-in only when reading that source's existing published snapshot. Keep fresh collection and publication validation strict. Map legacy and new IDs to the same stable native identity, reject mixed-format and case-insensitive duplicates, and preserve creation/first-seen timestamps. Migrate data and metadata together only after a complete successful refresh and validation, retaining the expiry rules below. On failure, preserve the unchanged last-good data and success timestamp; do not normalize or rewrite legacy records as a failure side effect. Document the mapping and limited legacy-read opt-in in the source's own README; this exception does not relax website validation or authorize a repository-wide migration.

| Prior publication | Current outcome | Required effect |
|---|---|---|
| None | Valid nonempty collection successfully published | Atomically create data and metadata together; status `success` |
| None | Any failure | Create no folder, data or metadata; report sanitized failure in Action logs and issue evidence |
| Successful publication exists | New successful publication | Replace data with the validated, expiry-filtered dataset and update success metadata together; the dataset may be empty when every record from a valid nonempty collection has expired |
| Successful publication exists | Fetch/parse/validate/publish failure | Preserve last-good data and success timestamp; record failure metadata when possible |

### Expired-record cleanup — mandatory development and delivery gate

After successfully fetching and validating new records, every new or updated adapter must remove previously published records whose application deadline has passed from its own source's next published dataset. Publish the refreshed data and success metadata atomically; cleanup must not be a separate destructive write before successful publication. Filtering only the newly fetched records is insufficient if expired old records remain in the published dataset.

Determine expiry from supported, validated deadline fields and the publisher's documented timezone/date semantics. A date-only deadline remains open through the end of that date in the applicable timezone. Do not infer expiry from record age, absence from the latest response, or missing/ambiguous deadlines. Preserve the last-good dataset on fetch, parse, validation or publication failure, and never delete another source's records. Cleanup does not relax the valid nonempty collection requirement above. Validate the complete nonempty raw collection before filtering. If all validated collected records have expired, atomically publish an empty dataset and success metadata so old expired records cannot persist indefinitely. Distinguish this valid filtered-empty result from empty retrieval or invalid/incomplete collection, which remains a failure preserving last-good data. Published-snapshot validation must accept this empty dataset on subsequent runs; raw collection validation must still require nonempty complete records.

Delivery requires independent evidence that the successful refresh removes expired old records, retains eligible current records, and preserves last-good data on failure. Document source-specific expiry rules and cleanup behavior in the adapter's README. Static publication review verifies this behavior without production execution; the sole live collection test remains non-publishing.

Metadata contains source identity/attribution, `status` (`success` or `fail`), concise `message`, UTC ISO-8601 `last_attempt_at` and `last_success_at`, and a sanitized actionable `error` plus failure stage when known. Advance `last_success_at` only when valid nonempty retrieval is successfully published. Failure reporting must not erase prior source information or claim durable status was saved if metadata publication failed.

After first success, source metadata is the sole durable run-status record. Before first success, blocked or unsolvable sources have no published folder. Production publication begins after maintainer merge. Tests never publish or receive publication credentials; a collection test and static code review do not prove production publication.
