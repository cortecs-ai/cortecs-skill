# Cortecs skill

An [Agent Skill](https://agentskills.io) for building with [Cortecs](https://cortecs.ai), Europe's AI gateway. Works with Claude Code, Codex, Cursor, OpenCode, and other agents supported by [Vercel Skills](https://github.com/vercel-labs/skills).

## Install

Use Node.js 22.20 or later, as required by the current Skills CLI.

```bash
npx skills add cortecs-ai/cortecs-skill --skill cortecs
```

With Bun, use `bunx` in place of `npx` in any command here:

```bash
bunx skills add cortecs-ai/cortecs-skill --skill cortecs
```

Choose your agent when prompted. Installation is project-scoped by default; add `-g` for user-wide installation or `-a claude-code` / `-a codex` to select an agent.

Preview available skills:

```bash
npx skills add cortecs-ai/cortecs-skill --list
```

To try this checkout before publishing, run from the project where you want the skill installed:

```bash
npx skills add /absolute/path/to/cortecs-skill --skill cortecs
```

The repository is the installable package; no custom npm package or API credentials are needed to install it. API requests require your own Cortecs key.

### Claude Code plugin

After publishing this checkout to GitHub, install through the bundled marketplace:

```text
/plugin marketplace add cortecs-ai/cortecs-skill
/plugin install cortecs@cortecs
```

Invoke the plugin skill as `/cortecs:cortecs`, or let Claude select it when relevant. For a local preview before publishing, launch Claude Code from this checkout:

```bash
claude --plugin-dir .
```

[.claude-plugin/plugin.json](.claude-plugin/plugin.json) declares the plugin; [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) makes the repository a marketplace containing it. Both use the existing `skills/` directory through Claude's [standard plugin layout](https://code.claude.com/docs/en/plugins-reference#standard-layout).

This supports a repository-hosted marketplace. Submission to Anthropic's public plugin directory is separate and requires a declared license; its validator also recommends a listing icon.

### Cursor plugin

[.cursor-plugin/plugin.json](.cursor-plugin/plugin.json) packages the same `skills/` directory as a native Cursor plugin using [Cursor's plugin format](https://cursor.com/docs/reference/plugins). This prepares the repository for Cursor distribution; it does not publish a marketplace listing. Use the `npx skills` route with `-a cursor` for direct skill installation.

Choose either a native plugin or direct skill installation per agent to avoid duplicate copies of the same instructions.

## Coverage

| Area | Included guidance |
| --- | --- |
| API integration | Python, JavaScript, cURL, Responses, Chat Completions, Anthropic Messages, migration, streaming, tools, structured output |
| Model discovery | Exact IDs, capability and provider inspection, pricing, pinned versions, `:latest`, project presets |
| Routing | Speed/cost/balanced, provider allowlists and ordering, fallbacks, quantization, reasoning, prompt caching |
| Multimodal and retrieval | Images and PDFs, audio inputs, embeddings, rerank, image generation/editing, transcription, speech, OCR, decisions/System One |
| Integrations | Vercel AI SDK, LangChain, LlamaIndex, LiteLLM, Pydantic AI, Langfuse; coding agents, automations, chat and workplace apps |
| Administration | Keys, teams, inference settings, budgets, presets, notifications, billing, usage, logs, IP restrictions, BYOK |
| Data controls | EU sovereignty, zero data retention, enforced settings, professional secrecy prerequisites and BYOK boundaries |
| Troubleshooting | Authentication, provider capability mismatches, request shapes, budgets, retries, cost units, streaming failures |

Try prompts such as:

- “Migrate this OpenAI client to Cortecs and preserve streaming and tools.”
- “Use Cortecs with the Vercel AI SDK, with EU-native and ZDR routing.”
- “Build a retrieval pipeline using Cortecs embeddings and reranking.”
- “Connect Claude Code to Cortecs.”
- “Inspect team budgets and diagnose why a Cortecs request failed.”

The entrypoint is [skills/cortecs/SKILL.md](skills/cortecs/SKILL.md). It loads the relevant references on demand. Model IDs, availability, pricing, and third-party integration settings are resolved from current official documentation rather than frozen into a model catalog.

## Validate

Use Python 3.11 or later for the offline check:

```bash
python3 tests/validate.py
npx skills add . --list
```

The offline check validates plugin metadata and marketplace paths, local Markdown links, and example JSON, Python, shell, and TOML syntax. JavaScript and TypeScript examples are checked with Bun when it is installed; without Bun, Node checks JavaScript only. It makes no API calls. For installer verification, install the local checkout into a temporary project and inspect the installed reference files.

With Claude Code installed, validate both native manifests:

```bash
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

## Sources

Written against [Cortecs documentation](https://docs.cortecs.ai/llms.txt) on 2026-11-05. Each reference links its supporting documentation.

Packaging follows [Vercel's skill format](https://github.com/vercel-labs/skills/blob/main/docs/creating-skills.md); [EUrouter](https://github.com/EUrouter/eurouter-skill) and [OpenRouter](https://github.com/OpenRouterTeam/skills) were consulted for orientation. Their provider-specific fields and endpoints do not apply to Cortecs.
