# Troubleshooting

Sources: [Compatibility](https://docs.cortecs.ai/api/api-compatibility), [Management API](https://docs.cortecs.ai/api/management-api), [Logs](https://docs.cortecs.ai/web-console/logs), [Routing](https://docs.cortecs.ai/routing/routing-concept), [Service status](https://status.cortecs.ai).

## Isolate the failure

Record the host/path, protocol, exact model, status, sanitized response error and available request/trace ID. Never print tokens, raw authorization headers, real document bodies, or full credential environments. Error bodies can differ across gateway, upstream provider, and endpoint; inspect the actual shape rather than assuming one universal `error.code` format.

Reproduce with synthetic input and only required parameters. Use the same key, team scope and mandatory routing restrictions. First inspect the authenticated catalog and effective settings; then make a small authorized inference request if needed. Add optional features back one at a time. Compare request traces with the top-level result, since a recovered provider failure may still appear in the logs.

## Symptoms and remedies

Status meanings can vary by provider. These are diagnostic directions, not a guarantee that every Cortecs endpoint uses the same status mapping.

| Symptom | Check and remedy |
| --- | --- |
| Authentication error / 401 | Confirm a nonempty Cortecs key is supplied to the correct host using the expected SDK auth. Remove accidental whitespace; check key revocation and deployment secret availability. Never print the key to confirm it. |
| Permission error / 403 | Check management-key flag, admin role, team assignment and IP whitelist. A management key does not confer an admin role. |
| Payment/budget error / 402 | Inspect actual error, balance and every applicable budget scope/period. BYOK spend is not capped by Cortecs EUR budgets. Do not retry a hard budget failure or raise a limit without the user's requested scope. |
| 404 or missing models | Check `/v1` duplication/omission, wrong protocol, exact model ID, preset scope, and policy filtering. A single-model lookup can return `null` when no allowed provider matches. |
| Invalid request / 400 or 422 | Compare body and content type with the specific endpoint schema. Remove unsupported optional fields, translate protocol-specific content/tool shapes, and inspect provider validation errors. These do not trigger model fallback. |
| No eligible provider | Inspect model/provider capabilities, allowlist, sovereignty/ZDR, quantization whitelist, context size, output-token limit, and enforced team settings together. Preserve required policy; choose a compatible model/provider. |
| Throttling / 429 | Inspect upstream quota/availability and retry headers when present. Provider throttling can occur even if no general platform rate limit is advertised. Use bounded backoff with jitter. |
| Timeout or 5xx | Check status, provider trace and client timeout. Evaluate provider/model fallback under the same policies; bound retries and total request duration. |
| Routing fields have no effect | Check `allow_overwrite`, API key team, top-level JSON placement, and whether the SDK/framework forwards the custom fields. |
| Empty content | Inspect finish/stop reason, refusals, tool calls, reasoning and output items. Tool-only or reasoning-heavy responses need not contain plain text. Raise output limits only when appropriate. |
| Truncated JSON | Inspect token limits and finish reason; do not accept partial JSON. Verify structured-output support and validate against the application schema. |
| Streaming stops or emits invalid data | Distinguish network chunks from SSE frames; inspect proxy buffering and cancellation; handle stream errors after headers. Do not blindly replay partial output or completed tools. |
| Implausibly high reported cost | Default inference cost is credits, 1,000,000 per EUR. OpenCode/LiteLLM may expect USD; follow their guide for `x-cortecs-cost-unit: USD`. Check units before adjusting budgets. |
| Unexpected model/version | Inspect model fallback, `:latest`, preset target and actual returned model. Pin exact IDs and disable model fallback when required. |
| Retrieval degrades after a model change | Check document/query embedding model and vector space, not just dimension. Re-embed consistently for an intentional migration. |
| A chat tool works but its app fails | Inspect background model slots, embeddings, built-in web search, unsupported storage/conversation fields and the app's configured protocol. |

## Retry boundaries

Use the existing SDK retry policy where possible; adding another retry layer can multiply attempts and cost. Retry transient connection failures, rate limits and eligible server failures with a bounded attempt count and deadline. Honor retry headers when available. Do not retry invalid credentials, permission failures, exhausted budgets, schema validation errors, or impossible provider policies unchanged.

Inference retries are not a guarantee of exactly-once billing or tool execution. Do not automatically repeat external actions, key creation, invitations, budget changes or billing operations on ambiguous timeouts. Reconcile the resulting state first. For streaming, restarting a partially consumed response requires explicit application handling.

## Escalation information

For unresolved failures, provide the timestamp/timezone, request or trace ID, endpoint, model/provider, status, sanitized error, and a minimal synthetic reproduction. Consult the [status page](https://status.cortecs.ai) or direct the user to `support@cortecs.ai`. Do not send a support message on the user's behalf unless asked.
