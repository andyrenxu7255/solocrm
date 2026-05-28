# SoloCRM Usage Reference

## First Move

Run:

```bash
solocrm doctor --json
```

If the backend is reachable, continue with:

```bash
solocrm capabilities
solocrm summary
solocrm graph recall --industry 能源 --domain 数据中台 --json
solocrm audit summary --json
```

## Write Path

Prefer these commands:

- `solocrm engagement create`
- `solocrm engagement update`
- `solocrm engagement advance`
- `solocrm artifact create`
- `solocrm graph fact`
- `solocrm graph rebuild`
- `solocrm export`

All writes should preserve audit logs through `/agent/actions`.

## Audit Path

Use these commands whenever you need traceability:

```bash
solocrm audit summary --json
solocrm audit list --agent-name hermes --page-size 20 --json
solocrm audit errors --json
solocrm audit get <audit_id> --json
```

If a write fails, inspect the latest error audit before retrying.

## Graph Recall

Use graph recall when the user asks for old cases, reusable material, similar customers, or cross-industry/domain reasoning.

```bash
solocrm graph fact --payload-json '{"industry":"能源","customer":"北京电力","domain":"数据中台","project":"数据治理项目"}'
solocrm graph recall --industry 能源 --domain 数据中台 --json
solocrm graph recall --customer 北京电力 --max-hops 2 --json
solocrm graph nodes --node-type customer --json
solocrm graph edges --relation-type in_industry --json
```

Default recall is 1 hop. Use `--max-hops 2` only for similar-case or reusable-experience questions. Read `shared_nodes`, `paths`, `evidence`, and `gate.policy` before using a recalled case.

## Raw Escape Hatch

Use `solocrm request` only when the higher-level command does not exist.

## Do Not

- Do not bypass the API by writing SQL directly during normal operation.
- Do not delete or mutate records without explicit user intent.
- Do not assume cloud spreadsheets or external CRMs are authoritative.
