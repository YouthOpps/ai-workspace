# Website data and build

Read for input handling, normalization, source pages, build changes and JSON output.

- On every build, discover sources under the selected `data-source/datas/` snapshot. Read each source's `data.json` and `metadata.json` from one consistent revision; transform and validate them into website render/search models. Derived indexes belong only in build output or temporary storage.
- Missing or malformed required production input is an actionable build error. Distinguish valid empty data from missing input; do not fabricate opportunities or silently substitute another upstream contract. Fixtures belong in temporary test storage, never either upstream checkout or real listings.
- No upstream aggregate index is required or created. Never edit, repair, commit or push data-source.
- Build `/sources/` from metadata, exposing available public identity/name, description, official website, country, success/fail status, error explanation, attempt/check/success dates, counts and attribution. Render additional public fields without inventing values; absent facts are unknown. Escape text, validate links and redact secrets/personal data from diagnostics.
- Retain last-good records after collection failure and show latest failure separately from last success. Collection success does not establish application availability. Do not replace metadata truth with a guessed status.

## JSON serialization and acceptance

Source-controlled website JSON uses two-space indentation, UTF-8, LF and one final newline. Every production build emits minified JSON, including generated indexes and copied public assets: no insignificant whitespace outside strings, with one final newline allowed. Parse/serialize JSON; do not strip whitespace with regex or change strings, values, types or array order. Minify only output, preserving source JSON, upstream schemas and pinned inputs.

For build changes run the production build, inspect all emitted JSON for compact serialization, compare parsed values before/after minification and verify source/upstream files were not rewritten. Integrate these checks into the existing website build/QA workflow when implementing this contract. Formatting/minification violations block acceptance; editing these rules alone does not establish implementation compliance.
