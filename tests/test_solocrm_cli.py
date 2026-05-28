from __future__ import annotations

import json

from solocrm_cli import solocrm as cli


class FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_doctor_json(monkeypatch, capsys):
    def fake_urlopen(req, timeout=None):
        if req.full_url.endswith("/health"):
            return FakeResponse('{"code":0,"data":"healthy","message":"success"}')
        if req.full_url.endswith("/agent/capabilities"):
            return FakeResponse(
                '{"code":0,"data":{"actions":{"create_engagement":"x","add_artifact":"y"}},"message":"success"}'
            )
        raise AssertionError(req.full_url)

    monkeypatch.setattr(cli.urllib.request, "urlopen", fake_urlopen)

    rc = cli.main(["--base-url", "http://example.test", "--json", "doctor"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["data"]["checks"]["health"]["ok"] is True
    assert "create_engagement" in payload["data"]["checks"]["capabilities"]["actions"]


def test_engagement_create_routes_to_agent_action(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {"code": 0, "data": {"target_type": "engagement", "result": {"name": "北京电力"}}, "message": "success"}

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(
        [
            "--base-url",
            "http://example.test",
            "--json",
            "engagement",
            "create",
            "--agent",
            "hermes",
            "--payload-json",
            '{"name":"北京电力","company":"北京电力","stage":"sales","owner":"Andy"}',
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["ok"] is True
    assert calls[0][0] == "POST"
    assert calls[0][1] == "/agent/actions"
    assert calls[0][2] == {
        "agent_name": "hermes",
        "action": "create_engagement",
        "payload": {
            "name": "北京电力",
            "company": "北京电力",
            "stage": "sales",
            "owner": "Andy",
        },
    }


def test_export_writes_file(monkeypatch, tmp_path):
    target = tmp_path / "export.json"

    def fake_request(self, method, path, *, body=None, query=None):
        return {"code": 0, "data": {"format": "solocrm-agent-context-v1", "tables": {"engagements": []}}, "message": "success"}

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(["--base-url", "http://example.test", "--json", "export", "--out", str(target)])

    assert rc == 0
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["format"] == "solocrm-agent-context-v1"


def test_doctor_json_flag_after_command(monkeypatch, capsys):
    def fake_urlopen(req, timeout=None):
        if req.full_url.endswith("/health"):
            return FakeResponse('{"code":0,"data":"healthy","message":"success"}')
        if req.full_url.endswith("/agent/capabilities"):
            return FakeResponse('{"code":0,"data":{"actions":{}},"message":"success"}')
        raise AssertionError(req.full_url)

    monkeypatch.setattr(cli.urllib.request, "urlopen", fake_urlopen)

    rc = cli.main(["doctor", "--json", "--base-url", "http://example.test"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["data"]["checks"]["health"]["ok"] is True


def test_doctor_returns_nonzero_when_unhealthy(monkeypatch, capsys):
    def fake_urlopen(req, timeout=None):
        raise cli.urllib.error.URLError("down")

    monkeypatch.setattr(cli.urllib.request, "urlopen", fake_urlopen)

    rc = cli.main(["doctor", "--json"])
    out = capsys.readouterr().out

    assert rc == 1
    payload = json.loads(out)
    assert payload["ok"] is False
    assert payload["data"]["ok"] is False


def test_audit_list_builds_filtered_query(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {
            "code": 0,
            "data": {"items": [], "total": 0, "page": 2, "page_size": 10, "total_pages": 0},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(
        [
            "--base-url",
            "http://example.test",
            "--json",
            "audit",
            "list",
            "--agent-name",
            "hermes",
            "--status",
            "error",
            "--target-type",
            "engagement",
            "--page",
            "2",
            "--page-size",
            "10",
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["ok"] is True
    assert calls[0] == (
        "GET",
        "/agent/audit",
        None,
        {
            "agent_name": "hermes",
            "action": None,
            "status": "error",
            "target_type": "engagement",
            "page": 2,
            "page_size": 10,
        },
    )


def test_audit_errors_forces_error_status(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {
            "code": 0,
            "data": {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(["--json", "audit", "errors", "--agent-name", "openclaw"])
    out = capsys.readouterr().out

    assert rc == 0
    assert json.loads(out)["ok"] is True
    assert calls[0][1] == "/agent/audit"
    assert calls[0][3]["agent_name"] == "openclaw"
    assert calls[0][3]["status"] == "error"


def test_audit_get_and_summary(monkeypatch, capsys):
    calls = []
    audit_id = "11111111-1111-1111-1111-111111111111"

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        if path.endswith("/summary"):
            return {
                "code": 0,
                "data": {"status_counts": {"ok": 1}, "action_counts": {}, "agent_counts": {}, "latest_errors": []},
                "message": "success",
            }
        return {
            "code": 0,
            "data": {"id": audit_id, "status": "ok"},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc_get = cli.main(["--json", "audit", "get", audit_id])
    get_out = capsys.readouterr().out
    rc_summary = cli.main(["--json", "audit", "summary"])
    summary_out = capsys.readouterr().out

    assert rc_get == 0
    assert rc_summary == 0
    assert json.loads(get_out)["ok"] is True
    assert json.loads(summary_out)["ok"] is True
    assert calls[0][1] == f"/agent/audit/{audit_id}"
    assert calls[1][1] == "/agent/audit/summary"


def test_graph_fact_routes_to_agent_action(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {
            "code": 0,
            "data": {"target_type": "graph_fact", "result": {"nodes": [], "edges": []}},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(
        [
            "--json",
            "graph",
            "fact",
            "--agent",
            "hermes",
            "--payload-json",
            '{"industry":"能源","customer":"北京电力","domain":"数据中台","project":"数据治理项目"}',
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert json.loads(out)["ok"] is True
    assert calls[0][0] == "POST"
    assert calls[0][1] == "/agent/actions"
    assert calls[0][2]["agent_name"] == "hermes"
    assert calls[0][2]["action"] == "upsert_graph_fact"
    assert calls[0][2]["payload"]["domain"] == "数据中台"


def test_graph_recall_builds_body(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {
            "code": 0,
            "data": {"query_nodes": [], "items": [], "gate": {"mode": "graph_first"}},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(
        [
            "--json",
            "graph",
            "recall",
            "--industry",
            "能源",
            "--domain",
            "数据中台",
            "--product",
            "SoloBI",
            "--city",
            "上海",
            "--query",
            "找同领域案例",
            "--limit",
            "5",
            "--max-hops",
            "2",
            "--no-artifacts",
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert json.loads(out)["ok"] is True
    assert calls[0] == (
        "POST",
        "/graph/recall",
        {
            "industry": "能源",
            "domain": "数据中台",
            "product": "SoloBI",
            "city": "上海",
            "query": "找同领域案例",
            "include_artifacts": False,
            "limit": 5,
            "max_hops": 2,
        },
        None,
    )


def test_graph_rebuild_routes_to_agent_action(monkeypatch, capsys):
    calls = []

    def fake_request(self, method, path, *, body=None, query=None):
        calls.append((method, path, body, query))
        return {
            "code": 0,
            "data": {"target_type": "graph_rebuild", "result": {"nodes": 3, "edges": 4}},
            "message": "success",
        }

    monkeypatch.setattr(cli.ApiClient, "request", fake_request)

    rc = cli.main(["--json", "graph", "rebuild", "--agent", "openclaw"])
    out = capsys.readouterr().out

    assert rc == 0
    assert json.loads(out)["ok"] is True
    assert calls[0][1] == "/agent/actions"
    assert calls[0][2]["action"] == "rebuild_graph"
