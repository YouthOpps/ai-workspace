# Adapter development

Read for assigned implementation/refactoring after the parent skill, collection/publication contract and workflow setup. Do not reread those documents if their current contents are already available.

1. Research the official publisher, opportunity inventory, permitted access, pagination and provenance. Review the adapter's complete collection-to-publication flow and downstream consumers before designing the change.
2. Implement the required behavior inside `adapter.py` under the architecture gate. Reuse local functions where useful, while keeping the folder independent of all other adapters. Put source-specific explanations in that adapter's `README.md`, leaving the repository root `README.md` unchanged, and remove obsolete scaffolds within scope.
3. Maintain the one live test. Validate all collected records under the embedded contract and emit the complete JSON to stdout; diagnostics go to stderr. Add no test framework, regression suite, fixture directory or Action test step.
4. Obtain independent QA using [testing](testing.md). Provide the revision, affected behavior and source evidence; do not substitute the author's pass for independent acceptance. Follow the workspace workflow for PR handoff or an independently assessed unsolvable attempt.

Changes to source access, metadata or publication must satisfy the contract even if ordinary collection still succeeds. Production Actions are not a test harness; implementation work does not authorize a production run.
