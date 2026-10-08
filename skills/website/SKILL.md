---
name: website
description: Develop, review or test the YouthOpps static website, including data ingestion, discovery, source transparency and responsive UI. Use for YouthOpps website work, not source adapters or unrelated sites.
---

# YouthOpps Website

Provider-independent instructions: follow the shared [agent scope](../../AGENTS.md#provider-independent-scope), including equivalent tools and independent review.

Read [workspace rules](../../AGENTS.md) once and use the matching [workflow route](../../docs/WORKFLOW.md). Review the requested revision without branch alignment. Implementation requires an assigned website issue; rules maintenance does not authorize product changes.

## Invariants

- Keep the three-project architecture: pipeline collects, data-source publishes, website transforms and presents a consistent data revision as a static site on Cloudflare Pages. Both data-source checkouts are read-only to website work; never repair or aggregate data upstream.
- Preserve the YouthOpp brand and established visual identity. Functional changes do not authorize redesign; an identity change needs explicit human authorization. Read the design reference for any visual change or visual review.
- Current website requirements override conflicting older website behavior/docs, while compatible workspace rules remain applicable. Keep implementation details and design/contribution/operations documentation in `website/docs/`.
- Use English project prose, factual source attribution and genuine data. Preserve original-language opportunity titles and intentional localization. Do not expose secrets or personal data from source diagnostics.

## Load only applicable references

| Changed or reviewed area | Required reference |
|---|---|
| Input discovery, normalization, metadata, build output, JSON | [Data and build](references/data-build.md) |
| Listings, search, filtering, pagination, expiry or detail pages | [Discovery](references/discovery.md) |
| UI, shared CSS/components, brand assets, responsive layout, rights/privacy/contact | [Design and trust](references/design.md) |
| Documentation, public rule links, automation, deployment | [Delivery](references/delivery.md) |
| Implementation acceptance or review of QA evidence | [Verification](references/verification.md), plus the affected area references |

Read multiple references for changes spanning their contracts, not every reference by default. During rules-only maintenance, inspect affected rules and consumers and validate internal/public links. Apply [code style](../../docs/CODE_STYLE.md) to authored code. Independent QA and handoff responsibilities remain in the workflow.
