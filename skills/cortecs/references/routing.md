# Routing and data controls

Contents: routing fields; enforcement; fallbacks; model aliases; reasoning; caching; governance.

Sources: [Routing](https://docs.cortecs.ai/routing/routing-concept), [Fallback](https://docs.cortecs.ai/routing/model-fallback), [Quantization](https://docs.cortecs.ai/examples/quantization), [Reasoning](https://docs.cortecs.ai/routing/reasoning), [Caching](https://docs.cortecs.ai/routing/prompt-caching), [Inference settings](https://docs.cortecs.ai/web-console/inference-settings).

## Request fields

These are top-level JSON body fields, or Python OpenAI SDK `extra_body` fields. Confirm support in the particular endpoint schema before forwarding a field to a non-chat API.

| Field | Meaning |
| --- | --- |
| `preference` | `"speed"`, `"cost"`, or `"balanced"` (default). Ranks eligible providers. |
| `allowed_providers` | Exact provider IDs forming an allowlist. No provider fallback outside it. Discover IDs from the model's providers, not display labels. |
| `provider_order` | `"custom"` tries `allowed_providers` in listed order instead of preference-based ranking. |
| `eu_native` | `true` restricts providers to those based and regulated within the EU. |
| `allow_zero_data_retention` | `true` restricts routing to ZDR endpoints; `false` permits endpoints with retention. |
| `quantizations` | Whitelist of endpoint precisions; omitted or `null` means no quantization whitelist. |
| `enable_model_fallback` | Enables/disables switching models when the primary cannot serve the request; documented default is `true`. |
| `fallbacks` | Ordered alternative **model IDs**, replacing the default model fallback chain. |

The general routing guide additionally documents `timeout` as router-side seconds, default 600; endpoint schemas may not enumerate it. Confirm it for the selected operation before relying on it. Configure SDK/HTTP timeouts separately: they govern the client, not provider ranking.

Example Chat body, replacing placeholders with discovered IDs before sending:

```json
{
  "model": "<EXACT_MODEL_ID>",
  "messages": [{"role": "user", "content": "Explain vector search briefly."}],
  "max_tokens": 128,
  "preference": "balanced",
  "eu_native": true,
  "allow_zero_data_retention": true,
  "enable_model_fallback": false
}
```

Filtering precedes ranking: policy, availability, context and output limits determine eligibility. A speed/cost preference cannot make an ineligible provider usable. Restricting providers or precisions can eliminate all endpoints; explain that conflict instead of relaxing requirements silently.

## Project and team enforcement

The API key's team determines its settings. The `Default` team holds global settings; other teams inherit them unless an explicit override exists. With **Allow overwrite** disabled, saved scope settings are enforced and individual request settings are ignored. With it enabled, requests may supply their own inference configuration.

For centrally enforced controls, read the current config first and update the applicable scope deliberately, preserving unrelated fields. `PUT /manage/project-configs?team_id=...` accepts `inference_config` and `allow_overwrite`. Disabling overwrite is what prevents callers from replacing required settings. Removing a custom team's config restores inheritance; it does not create unrestricted routing. See [management.md](management.md).

## Quantization

Supported whitelist entries: `int4`, `int8`, `fp4`, `mxfp4`, `nvfp4`, `fp6`, `fp8`, `mxfp8`, `fp16`, `bf16`, `fp32`, `unknown`.

`fp4` also matches `mxfp4` and `nvfp4`; `fp8` also matches `mxfp8`. A specific variant matches only itself. `unknown` admits endpoints without a declared precision. Unsupported entries match no endpoints. Do not include `unknown` when a known precision is required. Quantization may trade quality for speed/cost.

Use `quantizations` for new inference integrations. The deprecated `allow_quantization` boolean still appears in the management config schema; do not invent a `quantizations` management field until that schema supports it.

## Two kinds of fallback

Provider fallback retries another eligible provider for the same model. Model fallback changes the model after availability failures such as timeouts, outages, and rate limits. Invalid or unsupported parameters cause validation errors and do **not** trigger model fallback.

Default model chains follow family/version/size selection. A custom `fallbacks` array replaces the default chain and can cross model families. Supply `enable_model_fallback: true` when explicitly requesting a custom chain. `enable_model_fallback: false` requests the original model only; eligible same-model providers may still differ. Provider policies continue to apply.

Validate tools, output schemas, context limits and modalities across every fallback model. For embeddings, equal dimensions alone do not prove vector compatibility; pin the embedding model and disable model fallback when an existing index requires the same vector space. A deliberate embedding-model migration requires re-embedding the corpus and queries consistently.

The docs state only the successfully served model is billed; when all fallback models fail, the first attempted model's error is returned. Inspect the returned model/provider and request trace instead of assuming the primary served a successful response.

## Version aliases and presets

Sources: [Auto update](https://docs.cortecs.ai/routing/auto-update), [Presets](https://docs.cortecs.ai/web-console/presets).

- A discovered `<series>:latest` resolves to the newest published version immediately. Do not derive series names by truncating model IDs.
- Pin an exact ID for repeatable behavior and evaluate before upgrading.
- A project preset maps a stable alias to an exact or auto-update model ID. Create it with `alias` **without** `@`, then send inference requests with `model: "@alias"`.
- Updating the preset changes all its callers. Check use before changing/deleting it. Presets are model aliases, not named copies of arbitrary routing settings.

## Reasoning

Cortecs documents `reasoning_effort` values `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, and `max`; effective behavior depends on model/provider. For a requested unavailable level, Cortecs picks the next lower supported thinking level (excluding `none` unless explicitly requested), or the lowest higher level if no lower one exists. `none` cannot disable mandatory thinking; models without adjustable effort ignore the setting.

For Chat, use `reasoning_effort` through the SDK's supported parameter or custom body. Responses has a `reasoning` object; verify its supported shape for the selected model. Provider-specific `thinking`, `chat_template_kwargs`, or `output_config` are conditional controls, not universal replacements. Anthropic fixed thinking budgets must be below `max_tokens`; some newer models accept adaptive thinking only. Reasoning may increase cost and delay even without visible reasoning text.

## Prompt caching and cost

Caching is upstream and provider-dependent. Put stable system/tool/document prefixes first and variable user text later. Do not promise a cache hit, universal TTL, or shared cache across providers. Explicit cache markers are provider-specific; verify current syntax before using them. Retention restrictions still apply.

Chat usage may include `prompt_tokens_details.cached_tokens`, `cache_creation_tokens`, and `cost_details.cache_read_cost` / `cache_write_cost`. Input token totals already include cache tokens; avoid double counting. Default inference cost values are credits: divide by 1,000,000 to get EUR. Model catalog prices are separately denominated and measured per their documented unit. For an integration expecting USD response costs, Cortecs documents the `x-cortecs-cost-unit: USD` header; do not apply the default credit conversion to those returned fields.

## Governance boundaries

Sources: [Data governance](https://docs.cortecs.ai/security-and-compliance/data-governance-and-controls), [Sovereign Cloud](https://docs.cortecs.ai/security-and-compliance/sovereign-cloud), [ZDR](https://docs.cortecs.ai/security-and-compliance/zero-data-retention-zdr), [Professional secrecy](https://docs.cortecs.ai/security-and-compliance/professional-secrecy-agreement).

Cortecs documents European data residency and no training on managed traffic, with Cortecs acting as processor and managed providers as subprocessors. This does not make EU ownership, zero retention, certification, and workload-specific legal suitability interchangeable. Use the actual controls requested and attribute compliance claims to the current documentation and agreements.

For German § 203 protected information, the official guide requires **both** an effective Professional Secrecy Addendum **and** routing restricted to the current approved provider list. Default routing is unsuitable. Read that live list rather than freezing approved providers into code, and enforce required restrictions against overrides. An addendum alone does not configure routing.

BYOK provider accounts need independently established safeguards and agreements. Do not extend managed-provider guarantees to BYOK. See [management.md](management.md).
