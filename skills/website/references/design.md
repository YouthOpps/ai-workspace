# Website design and trust

Read for visual changes/review, responsive layout, assets, disclosures, analytics or contact flows.

## Brand baseline

Only an explicit human instruction authorizing the specific identity change may override this baseline. Feature work, bug fixes, accessibility or cleanup do not authorize rebranding. Do not edit the rule to legitimize an unauthorized redesign. Necessary identity changes and rights/provenance problems must be explained rather than silently replaced.

| Element | Required baseline |
|---|---|
| Identity | YouthOpp and configured brand wording |
| Assets | `/assets/youthopp-icon-v1.png` and `/assets/social-preview.png`; preserve pixels/proportions, including when filenames are unchanged |
| Palette in `website/assets/style.css` | Blue `#064cac` (legacy variable `--green`), text `#101725`, muted `#526078`, pale accent `#eaf0f8`, white `#ffffff`, borders `#d9dfe8`; retain semantic state/focus colors |
| Font | `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` |
| Presentation | Shared header/footer, existing hierarchy, restrained borders, spacing rhythm and simple institutional appearance |

No replacement/regeneration/recoloring/distortion of brand assets, alternate palette/theme/dark mode, page-specific brand overrides, substitute font/UI kit or decorative gradients/shadows/animations as a redesign. Reuse central settings and shared components. Functional/responsive/accessibility fixes may adjust implementation and local geometry while preserving these invariants.

Use viewport width up to 2048 px, then center content with growing gutters. Small readable internal spacing is allowed; no narrower desktop container. Check long content, small screens and widths below/at/above 2048 px for overflow and usable controls.

## Rights and transparency

Use openly licensed incorporated fonts, themes, icons and visual assets; verify provenance/reuse terms, preserve notices and document attribution concisely in `website/docs/`. System font fallback does not authorize font-file redistribution. External images and publisher logos are not presumed reusable.

Keep privacy, copyright, independent-index status, source attribution and external-site disclosures accessible and accurate. Optional analytics remain consent-gated; do not collect search text or sensitive data or assert legal compliance without evidence.

Explain source/link removal requests using verified project contacts and current configuration, including a private channel for sensitive requests. Requests receive human review; promise neither automatic removal nor obsolete pipeline routes. This does not authorize collection-repository edits.

Independent visual QA compares the pre-change appearance with the result and inspects CSS, branding settings and asset changes. Unauthorized drift blocks acceptance even when tests pass. For authorized identity changes, update this baseline and affected website docs together, keeping public rule links valid.
