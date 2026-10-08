# Website verification

Read for implementation acceptance and review of QA evidence. Rules-only maintenance requires instruction review and reference-link checks, not product UI certification.

Inspect the complete affected flow, reuse existing tests/utilities and run focused regressions plus required website test/build commands. Use temporary fixtures outside upstream repositories; identify fixture evidence explicitly. For build changes apply data/build serialization checks. A successful build or unit tests alone cannot establish UI acceptance.

Independent QA subagents must run browser UI tests against the built site, inspect rendered output and exercise affected interactions. Missing browser testing is a QA blocker for website implementation. Select the relevant cases below; changes to shared components or contracts expand affected coverage.

| Area | Cases to verify |
|---|---|
| Data/source pages | Per-source discovery and metadata, failure plus last-good data, unsafe values, empty/missing/malformed input |
| Discovery | Full-collection search, combined filters before pagination, preserved navigation state, accurate counts |
| Deadlines | Stable ordering, unknown dates, live expiry and returning to an open tab |
| Navigation/details | Correct source and original publisher links, factual details |
| UI | Responsive and keyboard behavior on representative mobile and desktop views; below/at/above 2048 px for visual changes |
| Visual changes | Pre-change comparison, shared CSS/brand/asset inspection against the design baseline |

Record the revision, commands, tested pages, viewports, actions, expected/observed results and screenshots or browser-test evidence. State coverage gaps, actual failures and any unverified live deployment. The working agent obtains independent acceptance under the workflow; do not recursively require reviewers to commission another review.
