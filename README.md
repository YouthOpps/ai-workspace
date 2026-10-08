# YouthOpps AI Workspace

Reusable project skills and a submodule-based development workspace for [YouthOpps](https://youthopps.org). Start with [AGENTS.md](AGENTS.md) for repository boundaries and task routing; [WORKFLOW.md](docs/WORKFLOW.md) owns the implementation, review and delivery lifecycle.

The instructions apply to Claude, Codex, Gemini and other AI agents. `CLAUDE.md` points to the same shared rules; provider-specific tool names and UI metadata are optional. Agents without native skill discovery can read the Markdown entry files directly. See [provider-independent scope](AGENTS.md#provider-independent-scope) for equivalent tools and independent review.

## Checkout

```sh
git clone https://github.com/YouthOpps/ai-workspace.git
cd ai-workspace
git submodule update --init --recursive
```

Development must occur in the owning workspace submodule, not a standalone clone. The workflow explains how to branch from current upstream while preserving local work and workspace pins. No issue is automatically assigned by this checkout.

| Directory | Purpose |
|---|---|
| `data-pipeline/` | Standalone source adapters; [Adapter skill](skills/adapter/SKILL.md) |
| `data-source/` | Publication-only data; no agent development or PRs |
| `website/` | Static site; [Website skill](skills/website/SKILL.md) |

## Skills

- **Adapter:** development, review and independent QA. Its entry file defines the required architecture and routes to the collection/publication contract, development or testing references.
- **Website:** development, review and QA. Its entry file routes to data/build, discovery, design, delivery or verification requirements according to the task.
- **[PR Review](skills/pr-review/SKILL.md):** portable PR review criteria and authorized English review publication; combine with the affected project's skill. This repository copy is authoritative; personal installations are convenience copies.

Read only applicable references. Common code style lives in [CODE_STYLE.md](docs/CODE_STYLE.md). The website's AI rules page links to authoritative files in this repository; keep those links valid without copying the rules into the website. Project prose is English. Skills are instructions for authorized work, not authorization to start product development or production execution.
