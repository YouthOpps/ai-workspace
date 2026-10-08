# Adapter review and independent QA

Read for adapter acceptance after the parent architecture gate and applicable [contract](contract.md). Use the workspace workflow for outcome ownership and issue/PR handoff. A reviewer checks their assigned evidence; independent reviewers do not recursively delegate the same review.

## Static review

- Establish the reviewed revision and affected paths. Verify the issue branch's upstream basis, unchanged workspace gitlink and repository scope from evidence; do not change the checkout to perform review.
- Apply the parent architecture gate using a complete baseline plus scoped rechecks. Check independent folder operation, imports, the sole live test and each matching Action's routing. No publication credentials or local/remote data writes in tests.
- Inspect the complete affected validation, metadata and publication path against the contract, including first-run failure, later failure preservation, atomic writes and pacing across overlapping runs. Read existing published data/metadata only when useful; do not invoke publication to test it.
- Check authored code style and the assigned adapter's README. Verify that new or updated adapters have their source explanations there, that `README.md` is the only additional file beyond the adapter/test pair, and that the repository root README has no changes. Unchanged older adapters without a README are not a migration requirement. Formatting tools stay outside data-pipeline and cannot add repository files or Action steps.

## Live evidence

Live evidence is required for acceptance of implementation changes affecting collection, runtime, validation, publication or data behavior. Documentation-only and static reviews assess relevant claims and existing evidence without starting collection or requiring unrelated live checks; they do not certify runtime behavior. Reuse valid evidence for unchanged behavior under the workspace workflow.

When live execution is required, run `python -B adapters/<pretty-source-name>/test_adapter.py` in the sandbox. If connectivity alone blocks it, retry only in an authorized networked environment. A blocked endpoint is not a passing test. Observe the contract's request allowance, including overlapping production runs; never invoke Actions or expose publication credentials.

Validate the complete stdout JSON in memory without creating output files. Use programmatic checks for every record and report count, validation failures, duplicates, coverage and representative first/last/edge records with publisher links. Independent QA must inspect actual record samples against the real inventory, not merely an exit code or count. Bound displayed output to relevant samples; do not paste an entire large dataset into model context. Expand inspection when samples, counts or source coverage reveal anomalies. If output is truncated before full validation, recover complete in-memory evidence or report the gap; never present a sample as full validation.

Verify titles, stable IDs, URLs, attribution, categories, countries, dates and completeness against the actual publisher, including pagination. A homepage/directory alone, synthetic records or unjustified inferred eligibility cannot establish acceptance. Report missing provenance and incomplete coverage.

## Decision

- **REJECT:** confirmed architecture, source quality/access, completeness, validation, pacing, failure handling, workflow, style, documentation or scope violation. Give reproducible evidence and requested correction.
- **BLOCKED:** material evidence or a plausible permitted access/testing route remains unavailable or pending. State what is needed.
- **ACCEPT (PR-ready):** checks required for the change's scope pass with independent evidence. Report revision, commands, sample links when live testing applies, coverage and limits. A documentation-only acceptance certifies the prose change, not runtime or production publication. This is not repository approval.
- **UNSOLVABLE:** use only the workflow's independently confirmed exhausted-attempt procedure, leaving the issue open and PR unmerged.
