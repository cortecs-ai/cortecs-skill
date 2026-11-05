# API and generation

Contents: protocol choice; model discovery; SDK setup; migration; streaming; tools; structured output.

Sources: [Compatibility](https://docs.cortecs.ai/api/api-compatibility), [Models](https://docs.cortecs.ai/api/models), [Responses](https://docs.cortecs.ai/api/responses), [Chat Completions](https://docs.cortecs.ai/api/chat-completions), [Messages](https://docs.cortecs.ai/api/anthropic-messages), [SDK examples](https://docs.cortecs.ai/integration-examples/tooling/openai-sdk).

## Protocol choice and endpoint map

All paths below are relative to `https://api.cortecs.ai/v1`.

| Method/path | Request | Result |
| --- | --- | --- |
| `GET /models` | Optional auth and capability/provider filters | `data[]` model catalog |
| `GET /models/{model_id}` | URL-encoded exact ID; optional auth/filters | Model with provider breakdown, or `null` when no allowed match exists |
| `POST /responses` | `model`, `input`; optional `instructions`, `max_output_tokens`, `tools`, `reasoning`, `text`, `stream` | Typed `output[]`; SDK `output_text`; typed events when streaming; beta |
| `POST /chat/completions` | `model`, `messages`; optional `max_tokens`, `tools`, `response_format`, `stream` | `choices[].message` or streamed `delta` |
| `POST /messages` | Anthropic format: `model`, `max_tokens`, `messages`; `system` outside messages | Content blocks or Anthropic stream events |

Do not mix `messages` with Responses `input`, `max_tokens` with Responses `max_output_tokens`, Chat `response_format` with Responses `text.format`, or their tool definitions and result envelopes. Translate deliberately when the user asks to switch protocols. The Responses schema lists `previous_response_id`, but does not document a managed conversation/storage service: do not promise persistent server-side history. Retain required history client-side when persistence is needed and verify continuation support for the chosen provider.

## Discover models before choosing one

```bash
curl --fail-with-body --silent --show-error --get \
  https://api.cortecs.ai/v1/models \
  -H "Authorization: Bearer ${CORTECS_API_KEY:?Set CORTECS_API_KEY}" \
  --data-urlencode 'tag=Code' \
  --data-urlencode 'extended=true'
```

Filters include `tag`, `currency` (default `EUR`), `allowed_providers`, `eu_native`, `quantizations`, and `allow_zero_data_retention`. Array parameters use the endpoint's query-array encoding; use repeated query keys for multiple values unless current documentation specifies otherwise. Tags include `Instruct`, `Code`, `Vision`, `Document`, `Image-Gen`, `Image-Edit`, `Audio`, `Speech`, `Embedding`, `Rerank`, `Transcription`, `OCR`, `Decision`, and `Reasoning`.

Inspect:

- `id`, `tags`, `input_modalities`, `output_modalities`.
- `context_size`, `max_output_tokens`, `supported_features` (`json_mode`, `reasoning`, `tools`).
- `providers` and `providers_details`: per-provider limits, features, quantization, pricing, and performance metrics. Metrics may be `null`.
- `pricing.currency` and unit-specific price fields. `input_token` and `output_token` are per **one million tokens**. Audio is per second, speech per million characters, OCR per thousand pages, images per image with possible additional megapixel charges. Model-level prices are minimums across providers, not a guaranteed routed price.

Use authenticated discovery with the same key and filters as the workload. Do not select the first model in the list blindly. Confirm the selected provider supports all requested features.

## Python

Use the existing `openai` dependency if available. The following is a complete Responses request:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cortecs.ai/v1",
    api_key=os.environ["CORTECS_API_KEY"],
)
response = client.responses.create(
    model=os.environ["CORTECS_MODEL"],
    input="Explain semantic search in one sentence.",
    max_output_tokens=128,
    extra_body={"preference": "balanced"},
)
print(response.output_text)
```

For a Chat Completions application, use the same `client`:

```python
completion = client.chat.completions.create(
    model=os.environ["CORTECS_MODEL"],
    messages=[{"role": "user", "content": "Say hello in German."}],
    max_tokens=64,
    extra_body={"eu_native": True, "allow_zero_data_retention": True},
)
print(completion.choices[0].message.content)
```

## JavaScript

Use the existing `openai` package when installed:

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.cortecs.ai/v1",
  apiKey: process.env.CORTECS_API_KEY,
});
const response = await client.responses.create({
  model: process.env.CORTECS_MODEL,
  input: "Explain semantic search in one sentence.",
  max_output_tokens: 128,
});
console.log(response.output_text);
```

For per-request routing outside the SDK's typed surface, use raw `fetch` instead of pretending Python's `extra_body` exists in JavaScript:

```javascript
const apiKey = process.env.CORTECS_API_KEY;
const model = process.env.CORTECS_MODEL;
if (!apiKey || !model) throw new Error("Set CORTECS_API_KEY and CORTECS_MODEL");

const response = await fetch("https://api.cortecs.ai/v1/chat/completions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model,
    messages: [{ role: "user", content: "Say hello in German." }],
    max_tokens: 64,
    preference: "cost",
    eu_native: true,
    allow_zero_data_retention: true,
  }),
});
if (!response.ok) throw new Error(`Cortecs request failed: HTTP ${response.status}`);
const result = await response.json();
console.log(result.choices[0].message.content);
```

## cURL

Replace `<EXACT_MODEL_ID>` with a discovered ID before sending:

```bash
curl --fail-with-body --silent --show-error \
  https://api.cortecs.ai/v1/chat/completions \
  -H "Authorization: Bearer ${CORTECS_API_KEY:?Set CORTECS_API_KEY}" \
  -H 'Content-Type: application/json' \
  --data '{"model":"<EXACT_MODEL_ID>","messages":[{"role":"user","content":"Say hello in German."}],"max_tokens":64}'
```

## Migration checklist

Keep the current protocol. Change the client base URL and secret source, resolve the model ID from Cortecs, and remove provider-specific options unsupported by Cortecs. Preserve message history, tool results, schema validation, streaming consumers, and retry limits. Remove old gateway routing objects and attribution headers; replace routing fields using [routing.md](routing.md). Update mocks that assert the host, path, headers, model, or usage currency. Do not change unrelated clients or globally replace shared `OPENAI_API_KEY` variables if those clients still use OpenAI directly.

## Streaming

Python Chat Completions, using the client above:

```python
stream = client.chat.completions.create(
    model=os.environ["CORTECS_MODEL"],
    messages=[{"role": "user", "content": "Write one short sentence."}],
    max_tokens=64,
    stream=True,
)
for chunk in stream:
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

Chat uses SSE data frames and delta objects; Responses and Messages use their own typed events. Prefer SDK parsing. Raw network chunks can contain incomplete or multiple SSE frames. Handle empty choices, tool-only deltas, terminal events, interruption, and errors after HTTP headers have been sent. If using optional final usage reporting, verify support for the selected protocol/provider and tolerate missing usage after cancellation. Do not silently restart a partially displayed response or re-execute completed tools.

## Tool calling

Source: [Tool calling](https://docs.cortecs.ai/examples/tool-calling).

Chat tools use `{"type":"function","function":{"name":...,"parameters":...}}`; Responses function tools place `name` and `parameters` directly beside `type`. Anthropic uses `name` and `input_schema`. Choose a model/provider advertising `tools`.

For a complete Chat tool turn: send tools and history; append the assistant message containing **all** tool calls; parse and validate each JSON argument against its schema; dispatch only allowlisted functions; append one `role: "tool"` message with matching `tool_call_id` and string content per call; request the next assistant turn. Handle no calls and multiple calls. Bound the loop and preserve error results. The model proposes execution; it does not authorize external actions. Never evaluate generated arguments as code.

Responses uses `function_call` output items and `function_call_output` input items matched by `call_id`. Messages uses `tool_use` and `tool_result` content blocks. Preserve provider-specific thinking/signature blocks when continuing a turn that requires them.

## Structured output

Source: [Structured outputs](https://docs.cortecs.ai/examples/structured-outputs).

Use Chat `response_format` with `type: "json_schema"` on a compatible provider. Python Pydantic parsing and JavaScript `zodResponseFormat` can reuse existing schema libraries; do not add one solely for a simple shape. JSON mode alone does not establish schema conformance. For Responses, read the current `text` configuration supported by the selected provider.

Validate parsed data before application use. Handle refusals, truncation, absent content, invalid JSON, and provider schema limitations. A model-level `json_mode` capability does not promise every JSON Schema keyword on every provider.
