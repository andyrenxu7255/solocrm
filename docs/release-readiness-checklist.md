# SoloCRM Release Readiness Checklist

Use this checklist before publishing a SoloCRM build or handing it to an OpenClaw, Hermes, or similar agent.

## Agent Contract

- `solocrm doctor --json` succeeds against the target backend.
- `solocrm capabilities` returns the supported action list.
- `docs/user-storylines.md` covers at least 10 distinct user paths, and the automated storyline tests pass.
- `solocrm summary` returns sales, presales, delivery, risk, and next-action context.
- Writes use `solocrm engagement ...`, `solocrm artifact ...`, or `POST /agent/actions`.
- Direct database writes are reserved for backup, restore, diagnostics, or explicit maintenance.

## Audit

- Successful agent writes create `agent_action_logs.status = ok`.
- Failed agent writes create `agent_action_logs.status = error`.
- `solocrm audit summary --json` returns status, action, and agent counts.
- `solocrm audit errors --json` returns recent failed actions.
- `solocrm audit get <audit_id> --json` returns the original request and result or error.

## Data Portability

- `solocrm export --out ./solocrm-export.json` creates a complete JSON export.
- Export includes `engagements`, `business_artifacts`, `graph_nodes`, `graph_edges`, and `agent_action_logs`.
- Contract templates, knowledge, proposals, delivery notes, and meeting notes are stored as artifacts.
- Sales, presales, and delivery state is stored in engagements.
- Industry, customer, domain, project, case, and artifact relationships are stored as graph facts.

## Graph Memory

- `solocrm graph fact --payload-json ...` can create explicit graph facts.
- `solocrm graph recall --industry <x> --domain <y> --json` returns cases or artifacts with shared nodes.
- Recalled items include `paths` and `evidence`.
- `solocrm graph rebuild --json` can rebuild graph memory after imports.
- Apache AGE remains optional; PostgreSQL graph tables are the default runtime path.

## Deployment

- Docker Compose starts backend, frontend, and PostgreSQL.
- `.env` contains database settings and optional OpenAI-compatible API settings.
- Local frontend builds use Node.js 20.19+ or 22.12+, matching the Docker builder.
- The CLI is installed with `python -m pip install -e .`.
- OpenClaw can read `OPENCLAW_INSTALL.md`, `AGENTS.md`, and `skills/solocrm/SKILL.md`.
- Hermes-style agents have `SOLOCRM_BASE_URL`, `SOLOCRM_TIMEOUT`, and `SOLOCRM_AGENT_NAME` configured.

## Verification Commands

```bash
python -m pytest -q backend/tests
python -m pytest -q tests
python -m py_compile solocrm_cli/solocrm.py backend/app/domains/agent/router.py backend/app/domains/business/router.py backend/app/domains/business/repository.py
cd frontend && npm audit --audit-level=high
cd frontend && npm run build
solocrm --help
solocrm audit --help
solocrm graph --help
solocrm doctor --json
```

## Promotion Criteria

- New users can deploy from the README without reading source code.
- Agents can operate using CLI commands without needing database credentials.
- Failed writes are visible through audit commands.
- Graph recall can explain why an old case or artifact is relevant.
- The system can be backed up or migrated through a single export.
