# Website documentation and delivery

Read for docs, public rule links, revision automation or deployment changes.

All website design, architecture, contribution and operations documentation belongs in `website/docs/`. Maintain a small set of concise guides with accessible static diagrams; update every affected authoritative section rather than adding historical reports or speculative design pages.

Maintain `website/docs/ai-rules.md` as a concise list of links to authoritative ai-workspace files on GitHub. Do not embed full rule copies or recreate a synchronization script. Keep entry links valid when files move; detailed references may be reached through the linked skill's routing table. Personal machine skills are not project publication sources. Local edits do not imply that the linked GitHub version has been published.

Preserve hourly automation checking for a newer data-source revision and updating the website only when data changes. The website submodule-cursor update triggers the Cloudflare Pages Git build; pipeline collection does not write to website. Each build processes `datas/` afresh. Scheduled execution can be delayed; do not promise exact hourly publication.

Keep deployment settings and data paths consistent with `website/docs/architecture.md` and other affected docs. Distinguish local build success, updated Git revision and confirmed deployment; do not claim live changes without deployment evidence. Use the workspace workflow for repository ownership, independent acceptance and maintainer handoff.
