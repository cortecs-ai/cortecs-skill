# Framework and application integrations

Contents: Vercel AI SDK; Python frameworks; coding agents; automation/chat/workplace guide index.

Use the application's existing dependency and preserve its protocol. Read the linked current Cortecs guide before editing a third-party application's configuration; keys, model names, file locations, and option names can vary by version. Merge configuration rather than replacing unrelated settings. Secrets belong in server environments or the application's credential store.

## Vercel AI SDK

Source: [Cortecs Vercel AI SDK guide](https://docs.cortecs.ai/integration-examples/tooling/vercel-ai-sdk).

Responses uses `ai` and `@ai-sdk/openai`:

```typescript
import { createOpenAI } from "@ai-sdk/openai";
import { generateText } from "ai";

const apiKey = process.env.CORTECS_API_KEY;
const model = process.env.CORTECS_MODEL;
if (!apiKey || !model) throw new Error("Set CORTECS_API_KEY and CORTECS_MODEL");

const cortecs = createOpenAI({
  name: "cortecs",
  baseURL: "https://api.cortecs.ai/v1",
  apiKey,
});
const { text } = await generateText({
  model: cortecs.responses(model),
  prompt: "Explain model routing in two sentences.",
});
console.log(text);
```

For Chat Completions with custom routing fields, use `@ai-sdk/openai-compatible`:

```typescript
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { generateText } from "ai";

const apiKey = process.env.CORTECS_API_KEY;
const model = process.env.CORTECS_MODEL;
if (!apiKey || !model) throw new Error("Set CORTECS_API_KEY and CORTECS_MODEL");

const cortecs = createOpenAICompatible({
  name: "cortecs",
  baseURL: "https://api.cortecs.ai/v1",
  apiKey,
});
const { text } = await generateText({
  model: cortecs.chatModel(model),
  prompt: "Explain model routing in two sentences.",
  providerOptions: {
    cortecs: { eu_native: true, allow_zero_data_retention: true },
  },
});
console.log(text);
```

The compatible provider forwards its provider options in the body; do not assume identical forwarding through the Responses provider. For enforced policy across clients, use saved Cortecs settings with overwrite disabled. For streaming, retain the application's existing `streamText` response adapter and verify how its installed SDK version emits tool/usage events.

## Python frameworks

| Framework | Cortecs connection | Important distinction |
| --- | --- | --- |
| [OpenAI SDK](https://docs.cortecs.ai/integration-examples/tooling/openai-sdk) | `OpenAI(base_url=..., api_key=...)` | See [api.md](api.md) for Responses and Chat examples; routing via `extra_body`. |
| [LangChain / LangGraph](https://docs.cortecs.ai/integration-examples/tooling/langchain) | `langchain_openai.ChatOpenAI(model=..., api_key=..., base_url="https://api.cortecs.ai/v1", extra_body={...})` | Preserve Chat Completions unless intentionally selecting Responses. Embeddings use `OpenAIEmbeddings`; check `model_kwargs` forwarding for installed version. |
| [LlamaIndex](https://docs.cortecs.ai/integration-examples/tooling/llamaindex) | `llama_index.llms.openai_like.OpenAILike(model=..., api_key=..., api_base="https://api.cortecs.ai/v1", is_chat_model=True)` | Set `is_function_calling_model=True` only for a model/provider with tools. Supply limits from discovery rather than another provider's model registry. |
| [Pydantic AI](https://docs.cortecs.ai/integration-examples/agents-and-automations/pydantic-ai) | `OpenAIProvider(base_url=..., api_key=...)` with `OpenAIResponsesModel` | Use `OpenAIChatModel` for Chat fallback. Avoid features requiring undocumented managed conversation storage. |
| [LiteLLM](https://docs.cortecs.ai/integration-examples/tooling/litellm) | Native `cortecs/<EXACT_ID>` model prefix, `CORTECS_API_KEY` | Prefix is LiteLLM's adapter selector; raw Cortecs requests use the unprefixed ID. Responses, completion and embedding helpers differ. |
| [Langfuse](https://docs.cortecs.ai/integration-examples/tooling/langfuse) | Instrument the existing Cortecs-configured SDK client | Application tracing can store prompts even if inference is ZDR. Configure redaction/retention explicitly for the user's requirements. |

LiteLLM example:

```python
import os
import litellm

response = litellm.completion(
    model=f"cortecs/{os.environ['CORTECS_MODEL']}",
    messages=[{"role": "user", "content": "Explain model routing briefly."}],
    extra_body={"preference": "balanced"},
    extra_headers={"x-cortecs-cost-unit": "USD"},
)
print(response.choices[0].message.content)
```

LiteLLM and OpenCode may interpret default credit-based costs as USD. The official guides prescribe `x-cortecs-cost-unit: USD` for those integrations. Follow the current guide for the installed adapter; retain the declared currency throughout reporting and budget calculations.

## Claude Code

Source: [Claude Code guide](https://docs.cortecs.ai/integration-examples/coding/claude-code).

Use a model/provider with tool calling. Set variables in the shell used to start Claude Code, with `CORTECS_MODEL` already set to a discovered ID:

```bash
export ANTHROPIC_BASE_URL="https://api.cortecs.ai"
export ANTHROPIC_AUTH_TOKEN="${CORTECS_API_KEY:?Set CORTECS_API_KEY}"
unset ANTHROPIC_API_KEY
export ANTHROPIC_MODEL="${CORTECS_MODEL:?Set CORTECS_MODEL}"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$CORTECS_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$CORTECS_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$CORTECS_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$CORTECS_MODEL"
claude
```

Claude Code adds `/v1/messages`; including `/v1` in this base URL can duplicate the path. Mapping all model slots prevents unintended default-model requests; use different compatible IDs only when the user needs them. Confirm the active base URL with `/status`. Do not write literal tokens into checked-in settings.

## Other coding agents

| Integration | Setup and caveat |
| --- | --- |
| [Codex CLI](https://docs.cortecs.ai/integration-examples/coding/codex-cli) | Add a Cortecs model provider with base URL `https://api.cortecs.ai/v1` and `wire_api = "responses"`; select an exact model ID. Read the installed Codex configuration reference for environment-backed credentials. Keep unsupported web search disabled only for the affected configuration/run, and select supported reasoning effort. |
| [OpenCode](https://docs.cortecs.ai/integration-examples/coding/opencode) | Native Cortecs provider: `opencode auth login`, select Cortecs. Follow the current guide to add `x-cortecs-cost-unit: USD`; configuration structure differs across versions. |
| [Kilo Code](https://docs.cortecs.ai/integration-examples/coding/kilo-code) | Use its documented Cortecs provider; choose embedding settings separately if enabling local indexing. |
| [Cline](https://docs.cortecs.ai/integration-examples/coding/cline) | Configure Cortecs as documented and use a discovered tool-capable model. |
| [GitHub Copilot](https://docs.cortecs.ai/integration-examples/coding/github-copilot) | Add a custom endpoint using the guide's expected URL and model capability metadata. |
| [Pi](https://docs.cortecs.ai/integration-examples/coding/pi) | Add the Cortecs provider/model to the supported custom provider configuration. |
| [Zed](https://docs.cortecs.ai/integration-examples/coding/zed) | Configure its OpenAI-compatible provider and model limits/tool support. Agent chat and edit prediction providers are configured separately. |

A tool requiring a full endpoint URL should receive `/v1/chat/completions` or `/v1/responses`; a tool asking for an SDK base URL usually needs `/v1`. Read the application's actual field definition to avoid doubling or omitting segments.

## Automations, chat, and workplace apps

Use this index to fetch the specific guide rather than loading every integration. For compatible HTTP modules, use Bearer authentication, `Content-Type: application/json`, an exact model, and the required request protocol. Do not fill OpenAI organization/project identifiers with Cortecs project IDs unless the integration explicitly requires that mapping.

| Integration | Relevant setup |
| --- | --- |
| [n8n](https://docs.cortecs.ai/integration-examples/agents-and-automations/n8n) | OpenAI credential: Cortecs base URL/key, organization blank. OpenAI Chat Model node; Responses enabled for new agent workflows, Chat fallback if required. |
| [Make.com](https://docs.cortecs.ai/integration-examples/agents-and-automations/make-com) | HTTP module and reusable authenticated keychain; POST to the full generation URL and map the protocol's output shape. |
| [Goose](https://docs.cortecs.ai/integration-examples/agents-and-automations/goose) | Custom compatible provider configuration. |
| [Hermes Agent](https://docs.cortecs.ai/integration-examples/agents-and-automations/hermes-agent) | Cortecs provider/base URL and tool-capable model. |
| [OpenClaw](https://docs.cortecs.ai/integration-examples/agents-and-automations/openclaw) | Follow provider onboarding and model configuration; preserve existing agent settings. |
| [AnythingLLM](https://docs.cortecs.ai/integration-examples/chat/anythingllm) | Generic OpenAI-compatible connection; configure embeddings separately. |
| [LibreChat](https://docs.cortecs.ai/integration-examples/chat/librechat) | Custom endpoint in its YAML configuration and a server-side environment key. Preserve mounts, model lists and parameter filtering. |
| [Open WebUI](https://docs.cortecs.ai/integration-examples/chat/open-webui) | Add OpenAI-compatible connection; embedding settings are separate from chat. |
| [LobeChat](https://docs.cortecs.ai/integration-examples/chat/lobechat) | Configure the documented compatible endpoint and exact model. |
| [Nextcloud Assistant](https://docs.cortecs.ai/integration-examples/workplace-apps/nextcloud-assistant) | Enable the required integration apps and configure the compatible provider. |
| [Camunda](https://docs.cortecs.ai/integration-examples/workplace-apps/camunda) | Store credentials in secrets and configure the connector endpoint/protocol. |
| [Mattermost](https://docs.cortecs.ai/integration-examples/workplace-apps/mattermost) | Add a compatible service and connect the intended agent. |
| [SAP Integration Suite](https://docs.cortecs.ai/integration-examples/workplace-apps/sap-integration-suite) | Store API credentials and configure the AI adapter. |
| [Zammad](https://docs.cortecs.ai/integration-examples/workplace-apps/zammad) | Configure the compatible provider for ticket AI features. |

For each integration, verify its smallest supported workload with synthetic input. Review secondary traffic—embeddings, background summarization, fallback model slots, telemetry, and tracing—when the user requires all AI processing to pass through Cortecs.
