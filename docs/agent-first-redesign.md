# SoloCRM Agent-First Redesign

## What Changed

The original SoloCRM repo was built around a single-person sales flow:
customer capture, visit prep, visit notes, MEDDIC review, and todo tracking.

That is useful, but it does not fully match the target you described:

- human users operate through agents
- the system must hold sales, pre-sales, and delivery in one structure
- contract templates, knowledge, and delivery assets must be portable
- the CRM should be local-first and migratable without a cloud spreadsheet

## New Core Model

### Engagement

One record for the full business process:

- sales
- presales
- contract
- delivery
- renewal
- closed

It holds stage, status, owner, value, next actions, risks, and domain JSON blocks.

### Business Artifact

Portable knowledge and delivery assets:

- contract templates
- proposals
- meeting notes
- delivery notes
- playbooks
- knowledge snippets

### Agent Action Log

Every agent command is logged so the system can be audited, replayed, and exported.

## API Surface

- `GET /agent/capabilities`
- `POST /agent/actions`
- `GET /business/summary`
- `GET /business/export`
- `GET/POST/PUT/DELETE /engagements`
- `GET/POST/PUT/DELETE /artifacts`

## Local-First Rules

- Data stays in PostgreSQL.
- Tables are created on startup.
- If no AI key is configured, structured CRUD and export still work.
- Embeddings are skipped instead of breaking writes.

## Validation Targets

- create and update an engagement
- add a portable artifact
- fetch a pipeline summary
- export all operational data
- verify the API works without cloud storage dependencies

