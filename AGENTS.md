# SoloCRM Agent Entry

> Context: SoloCRM is an agent-first local CRM for sales, presales, delivery, contracts, and knowledge.

## Critical Rules

- Use the HTTP API or `solocrm` CLI for normal reads and writes.
- Do not write directly to the database unless the user explicitly asks for maintenance or recovery.
- Keep agent actions auditable. Writes should go through `/agent/actions` or the CLI wrappers.
- After any failed write, inspect `solocrm audit errors --json` before retrying.
- The system is local-first. Do not assume any cloud spreadsheet or hosted CRM is the source of truth.
- Portable business data lives in `engagements`, `business_artifacts`, and `agent_action_logs`.

## First Commands

```bash
solocrm doctor --json
solocrm capabilities
solocrm summary
solocrm audit summary --json
solocrm export --out ./solocrm-export.json
```

## Documentation Map

- Deployment guide: `docs/agent-deployment-guide.md`
- API examples: `docs/agent-api-examples.md`
- Release readiness checklist: `docs/release-readiness-checklist.md`
- Skill: `skills/solocrm/SKILL.md`
- Current redesign notes: `docs/agent-first-redesign.md`

## Main Surfaces

- Health: `GET /health`
- Agent protocol: `GET /agent/capabilities`, `POST /agent/actions`
- Agent audit: `GET /agent/audit`, `GET /agent/audit/summary`, `GET /agent/audit/{id}`
- Business summary/export: `GET /business/summary`, `GET /business/export`
- Engagements: `/engagements`
- Artifacts: `/artifacts`
