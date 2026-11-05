# Project administration

Contents: roles and setup; management endpoint map; keys; inference settings; budgets; presets/teams; logs/usage; BYOK and IP restrictions.

Sources: [Admin quickstart](https://docs.cortecs.ai/admin-quickstart), [Member quickstart](https://docs.cortecs.ai/member-quickstart), [Management API](https://docs.cortecs.ai/api/management-api), [Web console](https://docs.cortecs.ai/web-console).

## Scope and roles

An admin configures funding, membership, settings and budgets. An invited member accepts the invitation using the invited email, selects the project, creates a key for an assigned team, and connects a tool. Members do not need to fund an already managed project themselves.

Management routes require a **management API key**. Admin-only operations additionally require the key owner's project admin role; a management key does not promote a member. Ordinary application traffic should use an inference key. Examples use a separate `CORTECS_MANAGEMENT_API_KEY` environment variable so management credentials do not accidentally become application defaults.

Read the current state and confirm target scope from the user's task before changing project settings, budgets, aliases, access, billing, or provider credentials. Keep authorization proportional to the requested operation; the skill itself grants no authority to delete keys, invite people, charge a card, or weaken policy. Never print returned secret key material to logs.

## Endpoint map

All paths below are relative to `https://api.cortecs.ai/v1`. Fetch the current management schema for exact bodies and role restrictions before mutations.

| Method | Path | Purpose |
| --- | --- | --- |
| GET / POST / DELETE | `/manage/api-keys` | List/create/delete the authenticated user's keys |
| GET / PUT / DELETE | `/manage/project-configs` | Retrieve/update effective team settings or remove a team override; optional `team_id` query |
| GET / POST | `/manage/presets` | List/create project model aliases; admin |
| PUT / DELETE | `/manage/presets/{alias}` | Retarget/delete alias; admin |
| GET | `/manage/notifications` | Catalog of notification rules and current project configuration |
| GET / PUT | `/manage/notifications/{rule_id}` | Retrieve/configure a notification rule |
| GET / POST / PUT / DELETE | `/manage/budgets` | Read/upsert/delete budget periods; mutations require admin |
| GET | `/manage/balance` | Current project balance and currency; admin |
| GET / POST / DELETE | `/manage/project-members` | List members/invitations, invite, remove/revoke; admin |
| GET / POST / DELETE | `/manage/teams` | List/create/delete teams; admin |
| GET / POST / DELETE | `/manage/teams/members` | List/assign/unassign team members; admin |
| GET | `/manage/logs` | Paginated traces including all attempts |
| GET | `/manage/usage` | Aggregated token/cost accounting |

Do not substitute OpenRouter's credits/keys endpoints or invent management routes for UI-only features. For bodies that include identifiers, retrieve the actual identifiers first rather than deriving them from display text.

## Keys and rotation

Source: [API keys](https://docs.cortecs.ai/web-console/api-keys).

Create a key with a unique `name`, optional `team_id`, and `is_management_key` (default `false`). Names allow letters, digits, hyphens, underscores and whitespace, up to 50 characters. `team_id` must belong to the authenticated user; omission defaults to the authenticating key's team, with legacy unassigned keys resolving to `Default`.

Create-body example:

```json
{"name": "production-backend", "team_id": "<ASSIGNED_TEAM>", "is_management_key": false}
```

Full key material is shown once. Store it directly in the intended secret store. Rotate by creating a replacement, updating consumers, verifying a successful request, and only then deleting the old key by `name`. Deletion removes associated budget configurations; recreate required limits for replacement keys. The API cannot delete the management key currently authenticating the deletion.

## Inference settings and team inheritance

Source: [Inference settings](https://docs.cortecs.ai/web-console/inference-settings).

Read the effective config for a particular team:

```bash
curl --fail-with-body --silent --show-error --get \
  https://api.cortecs.ai/v1/manage/project-configs \
  -H "Authorization: Bearer ${CORTECS_MANAGEMENT_API_KEY:?Set CORTECS_MANAGEMENT_API_KEY}" \
  --data-urlencode 'team_id=Default'
```

`Default` contains global configuration. Other teams inherit it unless overridden. Omitted `team_id` selects the authenticating key's team, **not necessarily Default**. Admins may retrieve any team; members only assigned teams. PUT is admin-only and accepts `inference_config` plus `allow_overwrite`. Read the existing config and preserve its unrelated values; do not assume PUT behaves as a partial patch.

The documented `inference_config` fields are `allowed_providers`, `eu_native`, `allow_quantization`, `max_tokens`, `preference`, `allow_zero_data_retention`, and `enable_model_fallback`. This management schema still uses `allow_quantization`; do not replace it with the inference-only `quantizations` field without updated documentation. Set `allow_overwrite: false` when the task requires central enforcement. DELETE removes a custom team's explicit override; Default cannot be removed.

## Budgets and billing

Sources: [Budgets](https://docs.cortecs.ai/web-console/budgets), [Billing](https://docs.cortecs.ai/web-console/billing), [Notifications](https://docs.cortecs.ai/web-console/notifications).

Budget `amount` is **EUR**, nonnegative, with up to two decimal places. It is not inference credits. Rules use `scope` (`project`, `team`, `user`, `api-key`) and `period` (`daily`, `weekly`, `monthly`). POST and PUT upsert one period; DELETE removes the selected period using its identifying fields.

| Target | Additional identifying fields |
| --- | --- |
| Project | No team/user/key target |
| One team / every team separately | `team_id: "<TEAM>"` / `team_id: "*"` |
| One user / all users separately | `user_id: "<USER_ID>"` / `user_id: "*"` |
| Every user in one team separately | Concrete `team_id`, omitted or `"*"` user ID |
| One API key | `key_name` and the owning `user_id` |
| Every key separately | `key_name: "*"`, `user_id` omitted or `null` |

Example upsert body for a project-wide monthly budget:

```json
{"scope": "project", "period": "monthly", "amount": 100.00}
```

Wildcard rules create separate counters, not one shared pool. For each period, a specific user's rule overrides a selected-team per-user rule, which overrides the all-users rule. Other applicable scopes still constrain the request. Reaching any applicable limit blocks requests until reset: midnight UTC daily, Monday 00:00 UTC weekly, first day 00:00 UTC monthly. A zero budget is an active blocking limit, not “unlimited.”

A funded project balance is separately required. Billing setup and auto top-up are console workflows; do not invent an API to charge/top up. Low-balance notifications help prevent interruption. Provider pricing, fee schedules, and payment options can change; use the current billing page rather than hardcoding commercial terms.

## Presets, teams, and membership

Sources: [Presets](https://docs.cortecs.ai/web-console/presets), [Teams](https://docs.cortecs.ai/web-console/teams).

Preset creation body is `{"alias":"support","model_id":"<EXACT_ID>"}`; inference uses `model: "@support"`. Alias syntax is lowercase letters/digits, `/`, and `-`, starts with a letter/digit, maximum 64 characters. PUT to the alias path accepts `model_id`. URL-encode the alias when constructing a path. Changing a preset affects existing callers.

Teams are identified with `team_id`; team creation/deletion bodies use that field. Default is system-managed and cannot be deleted. Team assignment uses `team_id` and a `user_ids` array. Users must retain at least one team: removing a final custom assignment restores Default; removing Default requires another membership. Inspect key assignment and dependent settings/budgets before deleting teams.

Member invitations accept `emails` and `role` (`member` or `admin`), up to 50 unique emails per request. Listing includes active users and pending/expired invitations, not a complete history of accepted invitations. Removing a member/revoking an invitation requires its actual identifier and current schema; do not send a guessed email-based delete shape.

## Usage and request diagnosis

Sources: [Usage](https://docs.cortecs.ai/web-console/usage), [Logs](https://docs.cortecs.ai/web-console/logs).

- `/manage/logs`: `range` defaults to `1h`, maximum 24h; `page` starts at 1; `limit` defaults to 50, maximum 100. Filters include `q`, `user_id`, `key_name`, `model`, `provider`, and integer `status`. Filters select traces, then all attempts for those traces are returned. A failed provider attempt inside a successful trace is not an overall failed request.
- `/manage/usage`: `from` defaults to UTC day start, `until` to now. Bucket values are `1h`, `1d`, `1w`, `1M`, `1Y`. `group_by` is comma-separated fields chosen from `team_id`, `user_id`, `key_name`, `model`, `provider`. Filters additionally include `byok`.
- Non-admin management keys are restricted to their permitted personal data; admins can inspect project-wide information. Preserve the response's declared units and avoid printing personal or sensitive trace metadata unnecessarily.

Use request logs for routing attempts and failures; use aggregated usage for spend and token totals. Keep request/trace identifiers for support without copying prompts or secrets into diagnostics.

## BYOK and network restrictions

Sources: [BYOK](https://docs.cortecs.ai/web-console/bring-your-own-key), [IP whitelists](https://docs.cortecs.ai/web-console/ip-whitelists).

BYOK is configured by admins in the console. “Prefer my key” tries the user's provider account first, then managed endpoints; “Fallback to my key” reverses that order. Both modes still require a Cortecs balance check. Provider charges apply, and Cortecs currently does not track EUR spend or enforce EUR budgets for BYOK-served requests. Configure independent provider-side spend controls.

Managed inference settings do not configure or establish the required safeguards in the user's upstream account. Verify provider-side region, ZDR, no-training terms, security and contractual requirements separately. Vertex uses a service-account JSON credential; Azure requires matching model deployment names; Bedrock's documented BYOK authentication currently uses Bedrock API keys. Consult the current page for supported providers and credential fields; do not copy secrets into examples or logs.

IP whitelists restrict project API access to trusted addresses/networks. For blocked traffic, check the actual outbound public IP, IPv4/IPv6 and proxy/NAT egress against the configured whitelist. Do not disable a whitelist globally as a troubleshooting shortcut.
