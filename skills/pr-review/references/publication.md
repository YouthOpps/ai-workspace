# Publish a PR review

Read after the assessment when publication is authorized. Use an available authenticated GitHub connector, API client or `gh` with equivalent review operations; no vendor-specific connector is required. Discover actual capabilities. Missing access means an unpublished draft, not a completed posting.

1. Refresh head SHA, open/closed state and current review activity. If the head changed, inspect new changes and reassess the verdict and line references before submitting. Do not review a closed/merged PR unless specifically requested.
2. Submit one cohesive English review with the appropriate event and inline comments where supported. Anchor comments to verified lines/sides on the reviewed diff and use the reviewed commit ID when supported. Unanchorable or metadata findings belong in the body. Avoid duplicate standalone summaries or unchanged findings already discussed.
3. Respect project reviewer-independence rules. For one's own implementation, use COMMENT and clearly label it a self-assessment; it cannot replace independent acceptance or recommend APPROVE as a workaround. If a platform limitation prevents an otherwise independent, authorized formal review, an ordinary comment may state the intended recommendation and limitation without claiming actual approval.
4. Verify submission through a confirmed review ID/URL or read-back. If the write outcome is unknown, inspect existing reviews before retrying. Stop on permission denial or an unverifiable outcome; preserve the draft rather than risking duplicate posts. If the head changes during submission, disclose that the review covers only the recorded SHA and reassess before claiming the latest revision is approved.

Scale the body to the findings. Include the decision and reviewed SHA, then evidence/corrections, optional suggestions if useful, validation/coverage limits and remaining approval conditions. Omit empty sections. Never claim tests, publication or approval without evidence.

Final response: link the submitted review or PR, give the verdict and disclose any publication failure. Local-only reviews should be clearly identified as unpublished.
