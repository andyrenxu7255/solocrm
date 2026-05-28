# SoloCRM Agent Deployment Guide

SoloCRM is meant to be operated by agents like OpenClaw or Hermes through a small, stable surface:

- deploy the stack locally or on your server
- verify the backend with `solocrm doctor`
- inspect capabilities before writing
- use CLI or HTTP API for audited changes
- export the full working context when migrating or backing up

## What the agent should use

Use this order:

1. `solocrm doctor --json`
2. `solocrm capabilities`
3. `solocrm summary`
4. `solocrm audit summary --json`
5. `solocrm engagement ...` or `solocrm artifact ...`
6. `solocrm audit errors --json` after a failed write
7. `solocrm export --out ...`

## OpenClaw Deployment

The repo already ships `openclaw-command.json` and `deploy.sh`.

Recommended OpenClaw flow:

1. Clone the repo into the OpenClaw workspace.
2. Start the stack with the deployment command.
3. Point the agent at the backend URL, usually `http://localhost:8000`.
4. Install or expose the `solocrm` CLI on the same machine.
5. Confirm the agent can call `solocrm doctor --json`.
6. Add `skills/solocrm/SKILL.md` to the agent skill roster or copy it into the OpenClaw skill directory.
7. Add the rules from `AGENTS.md` to the agent workspace instructions.

## Hermes Deployment

For Hermes-style agents, configure the same backend URL and expose the CLI in PATH.

Recommended environment variables:

```bash
SOLOCRM_BASE_URL=http://localhost:8000
SOLOCRM_TIMEOUT=15
SOLOCRM_AGENT_NAME=hermes
```

Expose these commands to Hermes as shell tools or approved CLI actions:

- `solocrm doctor --json`
- `solocrm capabilities`
- `solocrm summary`
- `solocrm engagement create|update|advance|get|list`
- `solocrm artifact create|get|list`
- `solocrm graph fact|recall|rebuild|nodes|edges`
- `solocrm audit summary|list|errors|get`
- `solocrm export --out <path>`

## CLI Installation

Install the CLI from the repo root:

```bash
python -m pip install -e .
```

Then verify:

```bash
solocrm --help
solocrm doctor --json
```

If you already have a broken `solocrm` command from an old install, reinstall this repo after uninstalling the stale one.

## Frontend Build

The Docker frontend builder uses `node:20.19-alpine` because Vite 7 requires Node.js 20.19 or newer. For local frontend development, use Node.js 20.19+ or 22.12+ before running:

```bash
cd frontend
npm ci
npm run build
```

## DB Access Policy

The normal path is API/CLI. Use direct database access only for:

- backups
- restore drills
- diagnostics
- explicit human-approved maintenance

Example psql entry:

```bash
docker compose exec db psql -U ${POSTGRES_USER:-solocrm} -d ${POSTGRES_DB:-solocrm}
```

The CLI also exposes `solocrm db info` for a quick reminder of the approved backup and psql paths.

## Graph Memory

Use graph memory for factual sales recall before broad semantic search.

The default deployment stores graph memory in PostgreSQL tables:

- `graph_nodes`
- `graph_edges`

This works on the standard `pgvector/pgvector:pg16` image. Apache AGE is optional. If you install AGE in PostgreSQL, set:

```bash
ENABLE_APACHE_AGE=true
```

AGE deployment notes:

- The Apache AGE site announces PostgreSQL 16 compatibility, and the official downloads page includes a PostgreSQL 16 release.
- The default Docker Compose file does not install AGE, so leave `ENABLE_APACHE_AGE=false` unless your PostgreSQL image already includes the `age` extension.
- Graph recall does not require AGE. AGE is reserved for deeper graph analytics and openCypher traversal once the operator chooses a graph-enabled PostgreSQL image.

Core commands:

```bash
solocrm graph fact --payload-json '{"industry":"能源","customer":"北京电力","domain":"数据中台","project":"数据治理项目"}'
solocrm graph recall --industry 能源 --domain 数据中台 --json
solocrm graph recall --product SoloBI --json
solocrm graph recall --city 上海 --json
solocrm graph rebuild --json
solocrm graph nodes --node-type industry --json
solocrm graph edges --relation-type serves_domain --json
```

Agent rule:

1. Use `solocrm graph recall` when preparing for a new customer.
2. Prefer recalled items that share explicit industry/domain/customer/project nodes.
3. Read `paths` and `evidence` before using an old case or material.
4. Use semantic search only after graph recall has defined a candidate set.

## Audit Trail

SoloCRM records every `/agent/actions` call in `agent_action_logs`.

Logged fields:

- `agent_name`
- `action`
- `target_type`
- `target_id`
- original request JSON
- result JSON or structured error JSON
- `status`, either `ok` or `error`
- `created_at`

Normal writes should go through the agent action endpoint or CLI wrappers so this audit trail stays complete.

Audit commands:

```bash
solocrm audit summary --json
solocrm audit list --agent-name hermes --page-size 20 --json
solocrm audit errors --json
solocrm audit get <audit_id> --json
```

When a write fails, the agent should:

1. Read the returned error message.
2. Run `solocrm audit errors --json`.
3. Fix the payload or action name.
4. Retry once with the corrected payload.
5. Stop and report the audit id if the second attempt fails.

## Useful Examples

Create an engagement:

```bash
solocrm engagement create --payload-json '{"name":"北京电力","company":"北京电力","stage":"sales","owner":"Andy"}'
```

Add a contract template:

```bash
solocrm artifact create --payload-json '{"artifact_type":"contract_template","title":"标准合同范本","content":"...","source":"hermes"}'
```

Export everything:

```bash
solocrm export --out ./solocrm-export.json
```
