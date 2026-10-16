# Adapter review and independent QA

Read for adapter acceptance after the parent architecture gate and applicable [contract](contract.md). Use the workspace workflow for outcome ownership and issue/PR handoff. A reviewer checks their assigned evidence; independent reviewers do not recursively delegate the same review.

## Static review

- Establish the reviewed revision and affected paths. Verify the issue branch's upstream basis, unchanged workspace gitlink and repository scope from evidence; do not change the checkout to perform review.
- Apply the parent architecture gate using a complete baseline plus scoped rechecks. Check independent folder operation, imports, the sole live test and each matching Action's routing. No publication credentials or local/remote data writes in tests.
- Verify the [daily schedule and pagination spacing contract](contract.md#daily-schedules-and-pagination-spacing): one daily cron, a distinct fixed slot in the source/site/workspace timetable, retained merge/manual guards and disabled holds, and complete pagination-path coverage including preloaded first pages. Measure the 12-second physical-start floor, at most five starts per rolling 60 seconds and the 30-second page-completion-to-next-page guard with real clocks. Verify increased physical/page spacing after 429, at least 30 minutes of backoff without valid Retry-After, exponential repeated-429 cooldowns, and preservation/restoration of stricter limits and durable state across failures/restarts. Check failure propagation, deferred callback/credential creation, preserved separate detail-request accounting and stricter publisher limits. Assess collection/phase/job and token-lifetime headroom. Local timing probes establish only their observed timing; they do not replace required native full-collection/consumer evidence or certify production publication. Reuse qualifying unchanged-behavior evidence only under the existing live-evidence rules.
- Inspect the complete affected validation, metadata and publication path against the contract, including first-run failure, later failure preservation, atomic writes and pacing across overlapping runs. Read existing published data/metadata only when useful; do not invoke publication to test it.
- Review the [factual-index and publisher-access policy](contract.md#factual-indexing-and-publisher-access): verify minimal factual output and original summaries, exact applicable restriction evidence, robots-purpose status classification through retries/redirects, retained real denials and backoff, and exact-run provenance for any scoped robots-only hold migration. Missing licences or generic rights notices alone are not blockers; this review establishes operational compliance, not legal clearance. Rules-only maintenance does not require publisher collection or production execution.
- Verify the [transport and durable access-state contract](contract.md#transport-and-durable-access-state) with actual-function inert controls outside the delivered tree: on HTTP 429, inspect the actual persisted strike count, increased physical/page gaps and embargo from inside the response body-read callback before returning any bytes or raising a body-read error; a finalizer-only check does not prove pre-body persistence. Verify that ordinary 429 stays timed while a visible challenge retains both cooldown and hold; malformed `Retry-After` alone creates no hold; challenges stop before redirect follow; robots redirects cannot relabel content; hidden/chrome text is excluded while primary refusals remain detected. Exercise mature owned-artifact restoration through the real transport function and ZIP decoding, including signature compatibility, ownership/digest checks and retained MAX constraints. Reject missing current runs, absent or mismatched job identity, mutable-update chronology and fallback after a newer attempt loses its artifact. Reuse qualifying unchanged native evidence under the live-evidence rules; these controls do not replace complete genuine collection or authorize production.
- Exercise actual request completion and owned-export functions with inert fault controls outside the delivered tree: after a complete successful response body, make the completion-journal write fail and verify sticky denial of subsequent publisher requests, including same-process collection/initialization re-entry, and refusal to export valid stale state. Independently fail unlink, failure-signal writing and both together; verify invalidation through a validated owned descriptor precedes those operations and leaves no valid stale JSON eligible for export. Confirm unexpected owners, unsafe permissions, symlinks and hard links remain untouched and refused. Include a healthy-path control retaining known stronger constraints. These controls do not replace qualifying native collection evidence or authorize publisher requests, publication or extra delivered test files.
- Exercise the actual physical transport with schema-valid high strike counts
  and extreme current physical/page intervals, including unsupported-clock or
  overflow failures while actual transport processes an inert 429 response.
  Inspect durable
  pending state before the opener, through header/body/REP decisions and after
  failures. Force actual REP-200 delay/Disallow and cached-new-target persistence
  failures before settlement; test permitted aliases, unavailable REP and raw
  byte provenance even when successful decoding yields empty text. Verify
  same-process reentry and a fresh module restoring an older
  settled ZIP cannot issue another publisher request. Use actual transport/ZIP
  decoding and MAX merge paths; helper-only arithmetic checks or an always
  rejecting public gate do not prove those paths. Report synthetic metadata/ZIP
  bindings as fixtures, not actual mature owned-state compatibility.
- Test parent-directory and journal-inode replacement, atomic rename followed by
  directory-fsync failure, in-place writes and the second member of a dual
  commit. Verify invalidation reaches the current owned inode under the original
  verified parent and preserves unrelated replacement objects. Combine journal
  invalidation and failure-marker/signal faults; verify fresh-process refusal.
  Missing or empty mature state must fail without a synthetic fresh budget.
- Trace actual opener/response classification through existing bounded retries:
  first ordinary no-response connection error then healthy 200, exhausted
  attempts, `HTTPError`, partial body reads, TLS and policy/storage failures.
  Inspect every actual inert physical start and completion gap, preserving
  ordinary retry bounds and refusing unsafe retries. Verify actual local pause
  checks before initialization and again after quiet before first publisher
  access when that coordination is required; fixtures supplement rather than
  establish the real workflow state. Check policy-state capacity against the
  full source frontier without discarding actual denials or adding a page cap.
- Verify the [crawler identity contract](contract.md#crawler-identity) across agent-authored source research/diagnostics and adapter requests, including final outbound headers in retries, redirects and live tests, product-token robots matching, legacy protective restrictions and the strictest applicable pacing. Check source-local constants and README access evidence; reject identity rotation, browser impersonation or state resets used to evade restrictions. Scope execution evidence to changed behavior and reuse qualifying unchanged evidence under the live-evidence rules below; a rules-only change requires no publisher requests or collection run.
- Trace every native-ID assignment and override through final validation. Verify the [ID contract](contract.md#collection), stable global identity and case-insensitive duplicate rejection on the final records. For an assigned migration, inspect the source-scoped legacy-read opt-in, native-identity mapping, mixed-format duplicate rejection, preserved creation/first-seen timestamps, successful atomic migration and unchanged last-good data on failure. Legacy acceptance must not reach fresh collection or publication validation.
- For incremental changes, verify the [incremental refresh contract](contract.md#incremental-refreshes): publisher-backed order/change coverage, overlap and equal timestamps, known/pinned records before unseen records, older edits/reopening/late additions, duplicate/page movement, truthful per-record timestamps, empty-delta fallback, complete-snapshot merging, expiry of old records, removals/full reconciliation, checkpoint loss and unchanged last-good data/checkpoint on failure. Use static traces or an in-memory harness outside the delivered adapter tree for scenario evidence; add no fixture/test files, mocked live collection or production invocations. Reject a first-known-ID shortcut without proven update coverage.
- Reject delivery if the [mandatory expired-record cleanup](contract.md#expired-record-cleanup--mandatory-development-and-delivery-gate) is absent or unverified. Inspect the successful refresh path and evidence showing removal of expired previously published records, retention of eligible current records, correct date/timezone boundaries, no inferred expiry for ambiguous deadlines, source isolation, successful atomic empty publication when all validated raw records have expired, subsequent reads of that empty snapshot, and last-good preservation on failure. Review publication statically; do not add publishing tests or invoke production Actions.
- Check authored code style and the assigned adapter's README. Verify that new or updated adapters have their source explanations there, that `README.md` is the only additional file beyond the adapter/test pair, and that the repository root README has no changes. Unchanged older adapters without a README are not a migration requirement. Formatting tools stay outside data-pipeline and cannot add repository files or Action steps.

## Native observer readiness

Before publisher access for an authorized native run, check any external
observer/controller privately, outside the delivered adapter tree:

- Bind the original test and imported adapter to the exact target folder,
  source identity and revisions. Run the actual consumer wrapper on a
  normalized positive with the expected source/folder/IDs, and a wrong-source
  negative that must fail. Compare complete input/output IDs; copying a wrapper
  or validator alone is not readiness.

- Read and call the original normalizer, expiry and metadata helpers using
  their actual call contracts and supported reference clock. An ISO string and
  a timezone-aware `datetime` are not interchangeable; use the source-specific
  arguments rather than a common signature.

- Compute readiness raw, current/expiry-filtered and valid-empty cases through
  those helpers with corresponding metadata; label fixtures synthetic. After
  genuine collection, check complete actual raw and filtered records and derive
  any expired-subset case only from actual records the original rule classifies
  as expired. Report when none exist. A derived empty envelope does not prove
  empty successful retrieval.

- Trace original assignments and prior-snapshot merge rules for `created_at`,
  `first_seen_at`, `updated_at`, `last_seen_at` and `last_checked_at`. Verify
  their actual roles; do not assume seen and checked timestamps are equal or
  advance together.

- Retain separate immutable outcomes, errors and revisions for the original
  test, observer process and external fixture/consumer checks. Never relabel a
  failed original test as passed. An external helper failure after
  original-test success is distinct. Correct pure offline harness defects
  against qualifying retained complete input without another publisher run,
  preserving the failure evidence and live-evidence rules below. Incomplete
  capture or changed source behavior is an evidence gap, not permission for an
  automatic retake.

These ordinary checks make no publisher requests, publish no data and add no
fixtures to the standalone adapter. They do not replace complete genuine native
evidence or require a new advanced fault campaign.

## Live evidence

Live evidence is required for acceptance of implementation changes affecting collection, runtime, validation, publication or data behavior. Documentation-only and static reviews assess relevant claims and existing evidence without starting collection or requiring unrelated live checks; they do not certify runtime behavior. Reuse valid evidence for unchanged behavior under the workspace workflow.

When live execution is required, run `python -B adapters/<pretty-source-name>/test_adapter.py` in the sandbox. If connectivity alone blocks it, retry only in an authorized networked environment. A blocked endpoint is not a passing test. Verify actual physical outbound starts against the contract's minimum gap and rolling-window allowance across endpoints, retries, redirects, pagination, concurrent paths and overlapping production runs; reservations alone are not actual-start evidence. Report evidence coverage and gaps; a partial ledger cannot establish full-run compliance. Reuse qualifying unchanged-behavior evidence without requiring a redundant live run or new ledger solely for this check. Never invoke Actions or expose publication credentials.

For an incremental implementation, the sole native live test must still perform a complete actual nonempty full-scan collection without publication. Report incremental fetched records and the complete merged dataset separately; cached records, a partial delta or a no-change result cannot replace this complete live evidence. Review the changed incremental path and its scenario evidence in addition to the full-scan result.

Validate the complete stdout JSON in memory without creating output files. Use programmatic checks for every record and report count, validation failures, duplicates, coverage and representative first/last/edge records with publisher links. Independent QA must inspect actual record samples against the real inventory, not merely an exit code or count. Bound displayed output to relevant samples; do not paste an entire large dataset into model context. Expand inspection when samples, counts or source coverage reveal anomalies. If output is truncated before full validation, recover complete in-memory evidence or report the gap; never present a sample as full validation.

For an authorized native run, retain its complete actual input privately in
RAM: all physical request starts/completions, response headers and returned body
segments (including available partial bytes on read failure), original stdout,
and every persistence attempt with resulting journal/RAM state snapshots. Record
capture availability/lifetime. Bind capture/controller and source revisions and
distinguish
physical attempts from policy-only transactions. Offline controller fixtures may
check instrumentation and fault paths, but must not replace genuine responses,
insert placeholder collection output, or be reported as a publisher collection.
When complete genuine input is retained and qualifies for unchanged-behavior
reuse, inspect/replay it with the exact changed code and current consumer; do not
retake publisher requests merely to repair a controller fixture. Report a real
coverage gap when capture is incomplete; changed collection still needs the sole
native live test under the existing acceptance rules.

Run the complete actual nonempty raw collection and the resulting actual expiry-filtered dataset, each with its corresponding metadata, through the current [website consumer](https://github.com/YouthOpps/youthopps.github.io/blob/main/scripts/data.mjs) in RAM, recording the consumer revision, complete input coverage and result. Include the valid filtered-empty data/metadata envelope when all validated raw records have expired; an empty published array does not substitute for nonempty raw collection evidence. Use the actual consumer rather than a copied validator, hand-built surrogate or hardcoded field count; preserve supported optional fields and public envelopes. A consumer harness may supply in-memory filesystem input outside the delivered adapter tree; it must not add dependencies or files to the standalone adapter. When valid prior complete native evidence qualifies for unchanged-behavior reuse, apply the exact changed code to every retained actual record and run this consumer check without claiming a new live collection. Failed, partial, sampled or synthetic evidence cannot substitute for complete actual records; changed collection behavior still requires the sole native live test above.

Verify titles, stable IDs, URLs, attribution, categories, countries, dates and completeness against the actual publisher, including pagination. A homepage/directory alone, synthetic records or unjustified inferred eligibility cannot establish acceptance. Report missing provenance and incomplete coverage.

## Decision

- **REJECT:** confirmed architecture, source quality/access, completeness, validation, pacing, failure handling, workflow, style, documentation or scope violation. Give reproducible evidence and requested correction.
- **BLOCKED:** material evidence or a plausible permitted access/testing route remains unavailable or pending. State what is needed.
- **ACCEPT (PR-ready):** checks required for the change's scope pass with independent evidence. Report revision, commands, sample links when live testing applies, coverage and limits. A documentation-only acceptance certifies the prose change, not runtime or production publication. This is not repository approval.
- **UNSOLVABLE:** use only the workflow's independently confirmed exhausted-attempt procedure, leaving the issue open and PR unmerged.
