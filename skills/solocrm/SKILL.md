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

4. Use graph recall before serious sales or presales preparation:

```bash
solocrm graph recall --industry 能源 --domain 数据中台 --json
```

5. Check audit health:

```bash
solocrm audit summary --json
```

6. Export everything before a risky change or migration:

```bash
solocrm export --out ./solocrm-export.json
```

## Safe Operating Rules

- Use `solocrm` or the HTTP API for normal work.
- Keep all writes auditable through `/agent/actions`.
- Treat `engagements` as the main business record for sales, presales, and delivery.
- Treat `business_artifacts` as the portable home for contracts, knowledge, proposals, and delivery notes.
- Treat `graph_nodes` and `graph_edges` as the fact memory for industry, customer, domain, project, case, and artifact recall.
- Use graph recall as the gate before broad semantic recall.
- Use direct database access only for backup, restore, or explicit maintenance.
- After a failed write, run `solocrm audit errors --json` before retrying.
- Stop after a second failed write and report the latest audit id to the user.

## Core Commands

### Read

- `solocrm engagement list`
- `solocrm engagement get <id>`
- `solocrm artifact list`
- `solocrm artifact get <id>`
- `solocrm graph recall --industry <industry> --domain <domain> --json`
- `solocrm graph nodes --node-type domain --json`
- `solocrm graph edges --relation-type serves_domain --json`
- `solocrm audit summary --json`
- `solocrm audit list --status ok --json`
- `solocrm audit errors --json`
- `solocrm audit get <id> --json`
- `solocrm summary`

### Write

- `solocrm engagement create --payload-json '{...}'`
- `solocrm engagement update <id> --payload-json '{...}'`
- `solocrm engagement advance <id> --stage delivery`
- `solocrm artifact create --payload-json '{...}'`
- `solocrm graph fact --payload-json '{...}'`
- `solocrm graph rebuild --json`

### Escape Hatch

- `solocrm request GET /agent/capabilities`
- `solocrm request POST /agent/actions --payload-json '{...}'`

### Database Help

- `solocrm db info`

## Failure Recovery

When a write command returns `ok: false` or an API envelope with `code: 1`:

1. Read the error message.
2. Run `solocrm audit errors --json`.
3. Correct the JSON payload, action name, or target id.
4. Retry once.
5. If it fails again, report the latest audit record and stop.

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
solocrm graph fact --payload-json '{"industry":"能源","customer":"北京电力","domain":"数据中台","project":"数据治理项目"}'
solocrm audit errors --json
solocrm export --out ./solocrm-export.json
```
