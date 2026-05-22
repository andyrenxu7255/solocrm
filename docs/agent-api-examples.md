# SoloCRM API Examples

All responses use the shared envelope:

```json
{ "code": 0, "data": {}, "message": "success" }
```

`code: 0` means success. `code: 1` means the request was accepted by the API layer but failed business validation. Failed agent actions are still written to the audit trail with `status: "error"`.

## Health

```bash
GET /health
```

## Agent Capabilities

```bash
GET /agent/capabilities
```

## Agent Actions

Create an engagement:

```bash
POST /agent/actions
{
  "agent_name": "openclaw",
  "action": "create_engagement",
  "payload": {
    "name": "北京电力数据中台",
    "company": "北京电力",
    "stage": "sales",
    "owner": "Andy",
    "priority": 2
  }
}
```

Add an artifact:

```bash
POST /agent/actions
{
  "agent_name": "hermes",
  "action": "add_artifact",
  "payload": {
    "artifact_type": "contract_template",
    "title": "标准交付合同范本",
    "content": "...",
    "source": "agent"
  }
}
```

Failed action example:

```bash
POST /agent/actions
{
  "agent_name": "openclaw",
  "action": "create_engagement",
  "payload": {
    "company": "北京电力"
  }
}
```

Expected response:

```json
{
  "code": 1,
  "data": null,
  "message": "1 validation error for EngagementCreate\nname\n  Field required"
}
```

After this, inspect `/agent/audit?status=error`.

## Agent Audit

List audit logs:

```bash
GET /agent/audit?status=error&page=1&page_size=20
```

Read one audit log:

```bash
GET /agent/audit/{audit_id}
```

Summarize audit health:

```bash
GET /agent/audit/summary
```

Summary shape:

```json
{
  "code": 0,
  "data": {
    "status_counts": { "ok": 12, "error": 1 },
    "action_counts": { "create_engagement": 4 },
    "agent_counts": { "hermes": 8 },
    "latest_errors": []
  },
  "message": "success"
}
```

## Export

```bash
GET /business/export
```
