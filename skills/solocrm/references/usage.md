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
```

## Write Path

Prefer these commands:

- `solocrm engagement create`
- `solocrm engagement update`
- `solocrm engagement advance`
- `solocrm artifact create`
- `solocrm export`

## Raw Escape Hatch

Use `solocrm request` only when the higher-level command does not exist.

## Do Not

- Do not bypass the API by writing SQL directly during normal operation.
- Do not delete or mutate records without explicit user intent.
- Do not assume cloud spreadsheets or external CRMs are authoritative.
