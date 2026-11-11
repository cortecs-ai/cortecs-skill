---
name: cortecs
description: Integrate, migrate to, configure, and troubleshoot Cortecs (cortecs.ai), the European AI gateway. Use when code or config mentions api.cortecs.ai or CORTECS_API_KEY, when migrating from OpenAI, OpenRouter, or EUrouter to Cortecs, and for Cortecs API requests, model selection, routing and fallbacks, multimodal or retrieval workloads, SDK and coding-agent setup, project administration, and EU sovereignty or zero data retention controls.
---

# Cortecs

Help the user complete their Cortecs task using the application's existing language, SDK, and conventions. Cortecs provides multiple compatible inference protocols and a separate management API. Compatibility is bounded by Cortecs' documented fields and the selected model/provider capabilities.

## Start with the task

Read only the reference relevant to the request:

| Task | Reference |
| --- | --- |
| First request, migration, model discovery, Python/JavaScript/cURL, streaming, tool calling, structured output, Responses vs Chat vs Messages | [API and generation](references/api.md) |
| Provider selection, sovereignty/ZDR, fallback, quantization, reasoning, caching, version aliases, presets | [Routing and data controls](references/routing.md) |
| Vision, PDFs, audio input, embeddings, rerank, image generation/editing, transcription, speech, OCR, decisions/System One | [Multimodal and retrieval](references/multimodal.md) |
| Frameworks, coding agents, chat, automation and workplace integrations | [Integrations](references/integrations.md) |
| Project setup, keys, teams, settings, budgets, billing, BYOK, usage and logs | [Administration](references/management.md) |
| Failed requests, unsupported features, retries, streaming and cost-reporting problems | [Troubleshooting](references/troubleshooting.md) |

## Connection essentials

| Setting | Value |
| --- | --- |
| OpenAI-compatible base URL | `https://api.cortecs.ai/v1` |
| Raw REST authentication | `Authorization: Bearer $CORTECS_API_KEY` |
| Anthropic SDK / Claude Code base URL | `https://api.cortecs.ai` (the client adds `/v1/messages`) |
| API key creation | [Console → Credentials](https://cortecs.ai/userArea/console?tab=credentials) |
| Model discovery | `GET https://api.cortecs.ai/v1/models` |
| Human-readable catalog | [Model catalog](https://cortecs.ai/serverlessModels) |

Use `CORTECS_API_KEY` for server-side secrets and `CORTECS_MODEL` for an exact, discovered model ID. These are example application environment-variable names, not an automatic configuration mechanism in every client. Never expose a key through browser code, public environment variables, logs, or checked-in configuration. Use an inference key for application traffic; management operations require a management key and may also require an admin role.

For a new agent workflow, prefer **Responses (beta)** if the client and model support it. Keep **Chat Completions** for existing clients or broad compatibility. Use **Anthropic Messages** for clients that speak that protocol. Do not change protocols merely to migrate a working application.

```bash
curl --fail-with-body --silent --show-error \
  https://api.cortecs.ai/v1/models \
  -H "Authorization: Bearer ${CORTECS_API_KEY:?Set CORTECS_API_KEY}"
```

Choose a returned `id` with the required modalities, context size, output limit, and features. Authenticated catalog results reflect the key's effective inference settings. Inspect `providers_details` with `extended=true` or the single-model endpoint when a capability or limit matters for a specific provider. Model-level capabilities describe the union of available providers, not a guarantee for every endpoint.

## Cortecs-specific invariants

- Put routing fields at the **top level of the request body**, not an OpenRouter/EUrouter `provider` object. Python's OpenAI SDK accepts these through `extra_body`; JavaScript can use raw `fetch` when typed SDK parameters do not expose them.
- Use exact Cortecs model and provider identifiers. Do not assume another gateway's model prefixes, aliases, headers, key formats, or management endpoints apply.
- `allow_zero_data_retention: true` restricts routing to ZDR endpoints. `eu_native: true` restricts providers to those based and regulated in the EU. These are distinct controls.
- Saved global/team settings take precedence when **Allow overwrite** is disabled. Do not weaken required controls to make a failed request succeed.
- `quantizations` is the current request whitelist. `allow_quantization` is deprecated for new inference requests, although the management configuration schema still documents that boolean.
- Provider retry and model fallback are different. `fallbacks` contains ordered **model IDs**; it replaces the default model fallback chain. Validation failures are returned without model fallback.
- Default inference `usage.cost` values are **credits**, with **1 EUR = 1,000,000 credits**. Model catalog prices carry their own currency and units; management budgets use EUR. Do not interchange these values.
- Do not infer OpenAI-managed storage, Files, Assistants, Batch, conversation resources, or durable response retrieval from “OpenAI-compatible.” Implement only documented Cortecs operations.
- BYOK has separate provider-side compliance obligations and currently lacks Cortecs EUR spend tracking and budget enforcement. Read the administration reference before recommending it.

## Keep facts current

Use the bundled references for task guidance, then consult the relevant official page before relying on volatile details. Start with [the documentation index](https://docs.cortecs.ai/llms.txt); append `.md` to a linked documentation page for Markdown. Use [the full documentation](https://docs.cortecs.ai/llms-full.txt) only when focused pages do not resolve the question. API pages embed OpenAPI schemas with exact paths, fields, and response shapes.

Prefer the specific endpoint schema and feature guide over a conflicting older example. If they disagree in a way that affects the task, describe the uncertainty and verify with a small authorized request; do not invent support. Read only the necessary pages. If network access is unavailable, use the local reference and identify what remains unverified.

## Finish the integration

Preserve existing request semantics, tool handling, streaming, timeouts, error handling, and data controls during migration. Update affected server configuration, environment templates, tests, and deployment secrets documentation. Test the changed behavior with mocked HTTP or existing tests first. A live smoke test, when within the user's request and credentials are available, should use synthetic data and a small output limit; report what was and was not tested.
