---
name: solocrm
description: Operate SoloCRM safely through its agent CLI and HTTP API. Use when an agent must inspect capabilities, create or update engagements, store contract or knowledge artifacts, export business context, or deploy/open the local CRM for OpenClaw, Hermes, or similar agents.
---

# SoloCRM

Use SoloCRM through the CLI first, then fall back to the HTTP API only when needed.

## Start Here

1. Check the backend:

```bash
solocrm doctor --json
```

2. Inspect the supported actions:

```bash
solocrm capabilities
```

3. Check the current business shape:

```bash
solocrm summary
```

4. Export everything before a risky change or migration:

```bash
solocrm export --out ./solocrm-export.json
```

## Safe Operating Rules

- Use `solocrm` or the HTTP API for normal work.
- Keep all writes auditable through `/agent/actions`.
- Treat `engagements` as the main business record for sales, presales, and delivery.
- Treat `business_artifacts` as the portable home for contracts, knowledge, proposals, and delivery notes.
- Use direct database access only for backup, restore, or explicit maintenance.

## Core Commands

### Read

- `solocrm engagement list`
- `solocrm engagement get <id>`
- `solocrm artifact list`
- `solocrm artifact get <id>`
- `solocrm summary`

### Write

- `solocrm engagement create --payload-json '{...}'`
- `solocrm engagement update <id> --payload-json '{...}'`
- `solocrm engagement advance <id> --stage delivery`
- `solocrm artifact create --payload-json '{...}'`

### Escape Hatch

- `solocrm request GET /agent/capabilities`
- `solocrm request POST /agent/actions --payload-json '{...}'`

### Database Help

- `solocrm db info`

## Environment

Use these when connecting to a remote backend:

```bash
SOLOCRM_BASE_URL=http://localhost:8000
SOLOCRM_TIMEOUT=15
SOLOCRM_AGENT_NAME=openclaw
```

## Examples

```bash
solocrm engagement create --payload-json '{"name":"北京电力","company":"北京电力","stage":"sales","owner":"Andy"}'
solocrm artifact create --payload-json '{"artifact_type":"knowledge","title":"客户会议纪要","content":"...","source":"hermes"}'
solocrm export --out ./solocrm-export.json
```
