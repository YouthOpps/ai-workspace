# Opportunity discovery

Read for lists, search, filtering, pagination, ordering, expiration and details.

- Use one shared listing interface and behavior for all opportunities, categories, destination-country lists, publisher/source-country lists and source-specific lists. Provide search and relevant filters throughout, including the source directory. Keep destination, publisher country and applicant eligibility distinct.
- Static search covers the entire selected collection, not just the visible page. Generate a suitably sized static index or equivalent at build time without requiring an application server. Apply query and filters before pagination; preserve state through navigation and show honest counts and empty states.
- Default order is due date ascending with stable ties; unknown deadlines follow dated records. Keep expired records visible, muted grey with a readable label. Recalculate expiry in browser JavaScript on load, over time and on returning to the tab; do not depend only on build time or upstream status. Document date-only/timezone handling. Missing dates imply neither expiry nor openness.
- Use previous/next, numbered pages, current-page indication and ellipses for long ranges. Links are keyboard accessible and preserve query/filter state; infinite scrolling does not replace pagination.
- Details show title, short factual description, relevant dates, source attribution and a clear original opportunity/publisher link. Preserve original-language titles, avoid copying copyrighted article text, and identify the original publisher as authoritative for application conditions.
