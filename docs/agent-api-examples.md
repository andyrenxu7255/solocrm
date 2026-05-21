# SoloCRM API Examples

All responses use the shared envelope:

```json
{ "code": 0, "data": {}, "message": "success" }
```

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

## Export

```bash
GET /business/export
```
