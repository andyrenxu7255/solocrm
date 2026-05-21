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
4. `solocrm engagement ...` or `solocrm artifact ...`
5. `solocrm export --out ...`

## OpenClaw Deployment

The repo already ships `openclaw-command.json` and `deploy.sh`.

Recommended OpenClaw flow:

1. Clone the repo into the OpenClaw workspace.
2. Start the stack with the deployment command.
3. Point the agent at the backend URL, usually `http://localhost:8000`.
4. Install or expose the `solocrm` CLI on the same machine.
5. Confirm the agent can call `solocrm doctor --json`.

## Hermes Deployment

For Hermes-style agents, configure the same backend URL and expose the CLI in PATH.

Recommended environment variables:

```bash
SOLOCRM_BASE_URL=http://localhost:8000
SOLOCRM_TIMEOUT=15
SOLOCRM_AGENT_NAME=hermes
```

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
