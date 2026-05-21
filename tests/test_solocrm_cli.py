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
