# Adapter collection and publication contract

Read for collection, validation, pacing, metadata, publication or corresponding review. The architecture is defined in the parent skill; lifecycle is defined in the workspace workflow.

## Collection

- Use permitted official publisher access and genuine opportunities; no synthetic records or unsupported eligibility inference. Honor terms, robots, approved access methods and stricter publisher limits.
- Each publisher's adapters and agent-authored research/diagnostic requests
  share at most five physical starts in any rolling 60 seconds. Wait at least
  12.2 seconds after the preceding physical publisher attempt completes,
  including response closure or error, before the next physical start across
  endpoints, retries, redirects, pagination and concurrent paths. Measure actual
  outbound starts and completions, not reservations or intended delays.
  Coordinate or serialize overlapping test/production runs under that same
  publisher allowance. Preserve native request history, backoff and stronger
  publisher limits. Different publishers need no shared allowance.
- After a received HTTP 429, double BOTH CURRENT retained physical-request
  spacing and inventory-page gap, retaining at least the 12.2-second physical
  and 30-second inventory floors and all stronger known constraints. Persist
  those gaps, the strike count and embargo before reading the bounded response
  body, then stop that collection without another publisher request. The next
  deadline is the maximum of the retained embargo, a valid `Retry-After` and
  at least 1,800 seconds from the response, increased exponentially for repeated
  observed 429s. A shorter valid `Retry-After` never reduces that fallback.
  Preserve restrictive pacing, request history, repeated-429 state, unknown
  historical provenance and backoff across process/hosted-run restarts; restore
  them before publisher access and after failures. A fresh runner or another
  adapter must not create a fresh allowance.
- Validate nonempty records, source identity, stable IDs, duplicate IDs, URLs, dates, attribution and classification inside the implementation. Preserve existing public field names and envelopes; do not introduce a separate/shared schema file.
- Final record IDs must match the current [website consumer](https://github.com/YouthOpps/youthopps.github.io/blob/main/scripts/data.mjs) grammar `^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$`. Use stable globally unique identities, normally the source slug followed by a stable native identifier or deterministic digest. Reject duplicates case-insensitively; colons, underscores, whitespace and other separators are invalid.
- Validate final IDs and all records after every native-ID assignment or override, before returning the complete collection and before publication. Earlier validation of an intermediate/generated ID does not validate the final native ID. Preserve identity across repeated collection; do not derive it from record order or mutable titles.

### Factual indexing and publisher access

The authorized product is a minimal public factual opportunity index: titles, basic factual fields, original source URLs and independently written brief summaries. Do not copy full publisher descriptions or images. Public visibility or Google indexing is not a blanket licence or legal waiver; this operational policy does not decide copyright, database rights, contractual enforceability or other legal questions.

Assess restrictions against the actual publisher, host/route, activity and intended output. Before blocking factual indexing on publisher terms, quote the exact clearly applicable automation or reuse clause and document its scope in the source README and issue evidence. Absence of an explicit licence, generic copyright/all-rights-reserved notices, or terms for a different service alone do not require permission or establish a prohibition. Preserve genuinely applicable express restrictions, including automated-collection bans and applicable database-extraction limits; unresolved applicability must be described accurately, without inventing a blanket legal conclusion or permission prerequisite.

For verified robots.txt retrieval only, treat HTTP 4xx responses other than 429, including 403/404/410, as unavailable REP rules under the selected [RFC 9309 policy](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.3), consistent with [Google's documented 4xx handling](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec#http-status-codes). Do not invent `Disallow` from these statuses or treat them as proof that content access or factual reuse is prohibited. Retain valid applicable explicit robots rules and other documented restrictions. Robots 429, `Retry-After` and existing embargoes retain rate-limit/backoff handling. Robots 5xx, TLS, DNS, timeout and other network failures are unreachable, not absent: stop or use valid cached constraints under [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.4), without converting an initial failure into unrestricted access. Actual content 401/403, 429 or challenge/refusal bodies remain access or rate-limit failures even when robots is unavailable; stop rather than bypass authentication or protections.

A legacy durable hold may be reclassified only through an explicitly scoped, independently reviewed migration with exact-run provenance proving it arose solely from a robots-only 403 and contains no other content refusal or applicable restriction supporting that hold. Preserve physical request history, pacing, `Retry-After`, backoff and stronger embargoes; unknown or mixed provenance must not be blindly cleared. Apply robots-purpose classification through transport, retries and redirects before writing durable refusal state. Any subsequent real content block stops retrieval and remains retained. This narrow recovery exception qualifies the retained-refusal and disabled-hold rules below; it does not itself authorize production execution or certify complete collection.

### Transport and durable access state

On HTTP 429, persist the doubled CURRENT physical/page gaps, strike count and
MAX embargo under the collection rule above before reading a bounded response
body, so a body-read failure cannot lose the cooldown. Stop the collection
without another publisher request. An ordinary rate-limit response remains a
timed restriction; a genuine visible human-verification challenge also retains
a durable access hold. Invalid, negative, nonfinite or stale `Retry-After`
values alone never create an access hold. The at-least-1,800-second exponential
fallback also applies when a valid header is shorter; preserve longer headers
and all stronger known constraints.

Persist a source-bound pending transaction before every physical publisher
request. Keep it pending through all response-header, body and applicable REP
assessment, including cached target-policy decisions and numeric/backoff
calculations. Settle only after every resulting restriction and completion is
durable, with evidence matching that actual transaction. Neither an older
settled snapshot nor a healthy finalizer may clear an unresolved request; do not
confuse transient pending snapshots of a proven completed transaction with a
newer unresolved attempt.

Any persistence failure in a reservation, restrictive response state or
completion, or an unassessed policy-calculation error, must latch publisher
access closed for the rest of that process, including collection/initialization
reentry. Unsupported counters, numeric overflow or unsupported clock values
after a 429 are unassessed failures, not
successful completion with older limits. Preserve known stronger constraints in
memory and the durable pending barrier. Even if invalidation and failure-marker
writes both fail, a fresh process must reject unresolved local/owned state;
restoring an older healthy ZIP must not clear it. Do not export valid stale state
or claim that best-effort cleanup established successful persistence.

Before error signalling or cleanup that can itself fail, invalidate stale exportable pacing state only through an already validated, identity-checked owned file descriptor, truncating and syncing it before signalling failure or attempting unlink. Do not follow, modify or remove unsafe paths, symlinks, multiply linked files, unexpected owners or files with unsafe permissions. Signal-write or unlink failures, individually or together, must not leave valid stale JSON eligible for export; cleanup success does not establish successful state persistence.

Bind journal I/O and invalidation to the originally verified parent directory
identity and use descriptor-relative operations with no symlink following.
Recheck parent/file ownership, permissions, link count and identity before
acknowledging persistence. Preserve replacement directories and unrelated or
unsafe files. After an atomic journal rename, invalidate the verified CURRENT
journal inode under that same parent; a retained descriptor to the unlinked old
inode does not invalidate the new file. In-place and dual journals must retain
their validated file identities, and partial dual commits must fail closed.

Preserve permitted bounded retries for an ordinary connection failure inside an
actual opener invocation before any response is received, while retaining one
pending owner and every physical reservation/completion gap. `HTTPError` counts
as a received response. Do not relabel a partial body read, TLS, namespace,
storage or unassessed policy failure as a new ordinary connection retry. Keep
existing retry/redirect bounds and document deliberately tightened error cases;
a policy-only transaction is not an extra physical request.

Inspect challenge bodies before following any content redirect, including 3xx responses. Determine refusal from primary visible content; hidden attributes, `aria-hidden="true"`, inline display/visibility suppression, script/template content and unrelated footer/navigation/aside text must not alone trigger a hold. Preserve genuine visible refusals within an otherwise normal publisher DOM. Robots-only status handling requires the literal `/robots.txt` path on each physical request: reject a robots redirect to another path before following it, and reject a robots-purpose flag on a content path before transport. Retain all other access and pacing protections above.

When hosted pacing restoration uses run history and owned artifacts, require the current run to be present and validate its workflow, source, head and attempt. Require explicit job identity fields to match the exact run/attempt/head, and order completed attempts by exact-attempt job completion times rather than mutable run `updated_at`. Restore the newest applicable attempt's exact owned state before publisher access; missing, expired, mismatched or incomplete state must fail closed without falling back to an older artifact or resetting restrictions. Any exceptional legacy migration still requires its separately scoped provenance and review.

Missing, empty, corrupt or unknown-schema state for an established source is
not a fresh allowance. Any exceptional first-state or legacy handoff for that
established source needs a scoped, independently reviewed
transition with exact provenance, preserving all known MAX restrictions and
explicit unknown history. Do not synthesize zero history, settled `False` or an
empty bootstrap merely because local state or the
newest owned artifact is absent.

When local collection relies on a production pause, verify the exact workflow
ID/path and disabled state before history/state initialization, then verify it
again after startup quiet immediately before the first real publisher request.
Keep the required serialization/pause for the complete run. A stubbed metadata
callback is not evidence of this actual local coordination check.

Bind scoped REP decisions to their actual targets and physical policy-body
provenance through permitted origin aliases. An unavailable policy must not reuse
a previous response's digest or fabricate a global content refusal.

Scale policy-observation storage without introducing a new source-frontier,
page or target cap. Any compaction must preserve actual denials, holds, pacing,
embargo MAX values, pending state and unknown history with independently checked
coverage. A bounded prototype is not permission to discard restrictions or
truncate collection to fit its state limit; require a separate source-specific
compatibility and capacity assessment before rollout.

Maintenance evidence: [OeAD's reviewed conditional 429 guard](https://github.com/YouthOpps/data-pipeline/pull/276#pullrequestreview-5540049593),
[three protocol prototypes](https://github.com/YouthOpps/data-pipeline/issues/273)
and the [NASA pacing investigation](https://github.com/YouthOpps/data-pipeline/issues/269).
These references distinguish private fault controls and preaccess review from
actual legacy compatibility, complete native collection and production proof;
they do not certify future source execution or authorize a broad migration.

### Incremental refreshes

Reduce redundant retrieval only when publisher evidence proves that an incremental scan preserves the source's documented inventory and update coverage. This is a source-specific optimization, not permission to truncate pagination or weaken validation. Document the selected mode and evidence in the adapter README; retain complete collection when a safe incremental boundary cannot be established.

- Prefer a documented change feed, durable cursor or modified-since filter with deterministic ordering, stable native IDs and a tie-breaker for equal timestamps. A publication-date-only filter does not cover edits to older calls. Persist the last successfully committed publisher watermark, not collection wall time or the newest local record alone. Use an evidence-based overlap window and match overlap against the baseline by native ID to cover equal timestamps, late indexing and backdated additions. Continue rejecting duplicate/conflicting fresh IDs and case-insensitive final-ID collisions; do not silently select conflicting versions without verified publisher version semantics; never advance the watermark after partial retrieval or failure.
- Stop pagination early only with verified ordering/change semantics and a proven boundary. One known ID is insufficient: pinned/promoted posts, reordered pages, duplicate entries, edited/reopened calls and late/backdated additions can occur behind it. When these cases are not covered by a documented publisher guarantee or another verified change path, continue the complete scan. No arbitrary page cap or assumption that page 1 is newest-first.
- Treat fetched changes as a delta, not a replacement snapshot. Merge by stable ID into the last-good validated source dataset, preserve creation/first-seen timestamps, validate the complete resulting dataset and apply expired-record cleanup to old and new records together. Keep unchecked records' per-record check/seen timestamps truthful. Do not drop untouched records merely because they are absent from a delta; use verified removal events or complete reconciliation for publisher removals.
- Commit the complete data and metadata atomically within the existing source-scoped pair; store the successful watermark and reconciliation state in that metadata envelope. Add no checkpoint/cache/sidecar files or dependencies. With no usable checkpoint, a missing/invalid baseline, an expired cursor or an ordering/schema change, perform a permitted complete refresh or fail while preserving last-good data. Never reset retained access refusals, pacing or backoff to recover a cursor. An empty delta must fall back to complete retrieval under the existing nonempty collection gate; if that cannot succeed, preserve last-good data, watermark and success timestamp and report failure. Do not claim a successful refresh, advance a checkpoint or perform expiry-only publication from an empty or incompletely retrieved delta.
- Set and document a finite full-reconciliation interval appropriate to the publisher, even when incremental runs succeed, to detect changes or removals outside the delta window. Persist and enforce when reconciliation is due; do not postpone it on every incremental success. A seven-day interval can be a starting point only when source evidence supports it. Keep normal schedules, request spacing and stronger publisher limits explicit and independently adjustable; fewer scheduled runs do not repair an individual timeout.

Keep the sole native live test as a complete actual nonempty full-scan collection without publication; a cached merged snapshot or partial delta cannot substitute for that evidence. Use static traces or an in-memory harness outside the delivered adapter tree for incremental scenarios, without extra test/fixture files, mocked live retrieval or production execution. Incremental behavior is accepted only with evidence for first-run complete retrieval, new additions, equal timestamps, known/pinned records before unseen records, edits/reopening/late additions, duplicate/page movement, no-change results, expired old records, deletions/reconciliation, checkpoint loss and failure preservation. If safe update coverage cannot be demonstrated, document why full collection remains necessary rather than shipping an early-stop shortcut.

### Daily schedules and pagination spacing

Each source workflow has one daily cron at a distinct fixed UTC time, selected randomly within a staggered timetable. Inspect the source, website-data-sync and workspace-sync workflow schedules before choosing a free slot; preserve existing assignments unless the task changes them. Do not randomize the cron on every run or add long random sleeps. Retain merge/manual triggers, repository/main guards and publication serialization; one daily scheduled event is not a one-run-per-day cap. Do not reactivate disabled access holds. GitHub may delay schedules, so distinct cron times alone do not guarantee non-overlap; retain the existing source publication queue.

Within a serialized collection, inventory pagination attempts wait at least
30 seconds after the preceding inventory page/physical attempt finishes before
the next inventory start. Cover the first-page entry, preloaded first pages,
taxonomy pages, AJAX continuations, sitemap partitions, retries and redirected
inventory hops. Keep this guard separate from the physical-request budget:
robots and detail requests do not inherit an inventory-only longer interval.
Sources without inventory pagination need no artificial page delay. Preserve
physical completion spacing, rolling limits, retry/redirect bounds, stronger
publisher limits, retained refusals and backoff. Coordinate overlapping tests
and production under the existing allowance; a process-local page guard alone
does not establish a shared page budget across machines.

Document the exact daily time and page-guard scope in each source README. Assess phase/collection/job limits and publication-token lifetime using complete relevant evidence before accepting slower paging; do not increase caps, clear backoff or weaken completeness to make validation pass. Native full-collection and consumer evidence requirements remain in force. Local timing probes prove only their observed request timing, not successful publisher collection or publication.

### Crawler identity

Every adapter and every agent-authored HTTP request to a source publisher must send exactly this header, across all providers and execution environments:

```http
User-Agent: YouthOppsBot/1.0 (+https://youthopps.org/bot/)
```

This covers source research, access diagnostics, collection, pagination, retries, redirects and live tests. Set and verify the final outbound header on every physical request, including requests created by transport wrappers or redirect/retry handlers; a local constant alone does not prove propagation. Keep the value local to each standalone adapter; do not introduce shared code or a framework. The public [bot information page](https://youthopps.org/bot/) describes this identity. This contract does not claim to configure platform tools or override vendor-managed browser/SDK identities; use an agent-controlled HTTP path when the header cannot be set and verified, or report that limitation. Preserve required authentication and proxy headers.

Evaluate robots rules for the `YouthOppsBot` product token and independently retain applicable legacy product-specific rules, persisted or documented protective refusals, and existing stricter fallback checks. A permission under the new or retained legacy product-specific rules must never override a refusal under the other; this does not require querying every historical identity's wildcard fallback when an explicit new product rule applies. Apply the most restrictive applicable crawl delay, request rate and other publisher limits together with the collection limits above. Preserve request history and backoff across retries, redirects and identity changes. Do not rotate identities, impersonate browsers, reset pacing state or otherwise use this identity change to evade robots restrictions, blocks or rate limits. Record source-specific access decisions in the adapter's own README.

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
