from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 15.0


class CliError(Exception):
    def __init__(self, message: str, *, code: str = "error", details: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details


class ApiClient:
    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | list[Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._url(path, query)
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw
            raise CliError(
                f"HTTP {exc.code} from {method.upper()} {path}",
                code="http_error",
                details=parsed,
            ) from exc
        except urllib.error.URLError as exc:
            raise CliError(
                f"Cannot reach SoloCRM at {self.base_url}: {exc.reason}",
                code="connection_error",
            ) from exc
        except TimeoutError as exc:
            raise CliError(
                f"Timed out reaching SoloCRM at {self.base_url}",
                code="timeout",
            ) from exc
        except json.JSONDecodeError as exc:
            raise CliError(
                f"SoloCRM returned non-JSON from {method.upper()} {path}",
                code="invalid_json",
            ) from exc

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{normalized}"
        if query:
            clean = {k: v for k, v in query.items() if v is not None}
            if clean:
                url = f"{url}?{urllib.parse.urlencode(clean, doseq=True)}"
        return url


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    try:
        parsed_globals, cleaned_argv = extract_globals(raw_argv)
    except CliError as exc:
        emit_error(exc, json_mode="--json" in raw_argv)
        return 1
    parser = build_parser()
    args = parser.parse_args(cleaned_argv)
    args.json = parsed_globals["json"] if parsed_globals["json"] is not None else args.json
    args.base_url = parsed_globals["base_url"] or args.base_url
    args.timeout = parsed_globals["timeout"] if parsed_globals["timeout"] is not None else args.timeout
    args.global_sources = parsed_globals["sources"]
    client = ApiClient(args.base_url, args.timeout)

    try:
        result = args.handler(args, client)
        overall_ok = True
        if args.command == "doctor" and isinstance(result, dict):
            overall_ok = bool(result.get("ok", True))
        emit(result, json_mode=args.json, ok=overall_ok)
        if not overall_ok:
            return 1
        return 0
    except CliError as exc:
        emit_error(exc, json_mode=args.json)
        return 1
    except KeyboardInterrupt:
        emit_error(CliError("Interrupted", code="interrupted"), json_mode=args.json)
        return 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solocrm",
        description="Operate SoloCRM through its agent-safe HTTP API.",
    )
    parser.add_argument("--json", action="store_true", help="emit stable JSON output")
    parser.add_argument(
        "--base-url",
        default=os.getenv("SOLOCRM_BASE_URL", DEFAULT_BASE_URL),
        help=f"SoloCRM backend URL, default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("SOLOCRM_TIMEOUT", DEFAULT_TIMEOUT)),
        help=f"request timeout in seconds, default: {DEFAULT_TIMEOUT:g}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="check CLI config and SoloCRM reachability")
    doctor.set_defaults(handler=cmd_doctor)

    capabilities = sub.add_parser("capabilities", help="show agent action capabilities")
    capabilities.set_defaults(handler=cmd_capabilities)

    summary = sub.add_parser("summary", help="show sales/presales/delivery summary")
    summary.set_defaults(handler=cmd_summary)

    export = sub.add_parser("export", help="export portable business context")
    export.add_argument("--out", help="write export JSON to this file")
    export.set_defaults(handler=cmd_export)

    action = sub.add_parser("action", help="run one audited agent action")
    action.add_argument("action", help="action name, such as create_engagement")
    action.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    add_payload_flags(action, required=False)
    action.set_defaults(handler=cmd_action)

    engagement = sub.add_parser("engagement", help="create, list, read, or update engagements")
    engagement_sub = engagement.add_subparsers(dest="engagement_command", required=True)
    engagement_list = engagement_sub.add_parser("list", help="list engagements")
    engagement_list.add_argument("--stage")
    engagement_list.add_argument("--status")
    engagement_list.add_argument("--page", type=int, default=1)
    engagement_list.add_argument("--page-size", type=int, default=20)
    engagement_list.set_defaults(handler=cmd_engagement_list)
    engagement_get = engagement_sub.add_parser("get", help="read one engagement")
    engagement_get.add_argument("engagement_id")
    engagement_get.set_defaults(handler=cmd_engagement_get)
    engagement_create = engagement_sub.add_parser("create", help="create engagement through audit log")
    engagement_create.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    add_payload_flags(engagement_create)
    engagement_create.set_defaults(handler=cmd_engagement_create)
    engagement_update = engagement_sub.add_parser("update", help="update engagement through audit log")
    engagement_update.add_argument("engagement_id")
    engagement_update.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    add_payload_flags(engagement_update)
    engagement_update.set_defaults(handler=cmd_engagement_update)
    engagement_advance = engagement_sub.add_parser("advance", help="move engagement stage through audit log")
    engagement_advance.add_argument("engagement_id")
    engagement_advance.add_argument("--stage", required=True)
    engagement_advance.add_argument("--status")
    engagement_advance.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    engagement_advance.add_argument("--next-actions-json")
    engagement_advance.add_argument("--risks-json")
    engagement_advance.set_defaults(handler=cmd_engagement_advance)

    artifact = sub.add_parser("artifact", help="create, list, or read portable artifacts")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_list = artifact_sub.add_parser("list", help="list artifacts")
    artifact_list.add_argument("--page", type=int, default=1)
    artifact_list.add_argument("--page-size", type=int, default=20)
    artifact_list.set_defaults(handler=cmd_artifact_list)
    artifact_get = artifact_sub.add_parser("get", help="read one artifact")
    artifact_get.add_argument("artifact_id")
    artifact_get.set_defaults(handler=cmd_artifact_get)
    artifact_create = artifact_sub.add_parser("create", help="create artifact through audit log")
    artifact_create.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    add_payload_flags(artifact_create)
    artifact_create.set_defaults(handler=cmd_artifact_create)

    audit = sub.add_parser("audit", help="inspect agent action audit logs")
    audit_sub = audit.add_subparsers(dest="audit_command", required=True)
    audit_list = audit_sub.add_parser("list", help="list audited agent actions")
    audit_list.add_argument("--agent-name")
    audit_list.add_argument("--action")
    audit_list.add_argument("--status")
    audit_list.add_argument("--target-type")
    audit_list.add_argument("--page", type=int, default=1)
    audit_list.add_argument("--page-size", type=int, default=20)
    audit_list.set_defaults(handler=cmd_audit_list)
    audit_errors = audit_sub.add_parser("errors", help="list failed agent actions")
    audit_errors.add_argument("--agent-name")
    audit_errors.add_argument("--action")
    audit_errors.add_argument("--target-type")
    audit_errors.add_argument("--page", type=int, default=1)
    audit_errors.add_argument("--page-size", type=int, default=20)
    audit_errors.set_defaults(handler=cmd_audit_errors)
    audit_get = audit_sub.add_parser("get", help="read one audit log")
    audit_get.add_argument("audit_id")
    audit_get.set_defaults(handler=cmd_audit_get)
    audit_summary = audit_sub.add_parser("summary", help="summarize agent audit health")
    audit_summary.set_defaults(handler=cmd_audit_summary)

    graph = sub.add_parser("graph", help="operate graph-gated business memory")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)
    graph_fact = graph_sub.add_parser("fact", help="upsert one graph fact through audit log")
    graph_fact.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    add_payload_flags(graph_fact)
    graph_fact.set_defaults(handler=cmd_graph_fact)
    graph_recall = graph_sub.add_parser("recall", help="recall cases and artifacts through graph gates")
    graph_recall.add_argument("--industry")
    graph_recall.add_argument("--customer")
    graph_recall.add_argument("--domain")
    graph_recall.add_argument("--project")
    graph_recall.add_argument("--product")
    graph_recall.add_argument("--city")
    graph_recall.add_argument("--query")
    graph_recall.add_argument("--limit", type=int, default=10)
    graph_recall.add_argument(
        "--no-artifacts",
        action="store_true",
        help="exclude business artifacts from graph recall",
    )
    graph_recall.set_defaults(handler=cmd_graph_recall)
    graph_rebuild = graph_sub.add_parser("rebuild", help="rebuild graph memory through audit log")
    graph_rebuild.add_argument("--agent", default=os.getenv("SOLOCRM_AGENT_NAME", "cli"))
    graph_rebuild.set_defaults(handler=cmd_graph_rebuild)
    graph_node_list = graph_sub.add_parser("nodes", help="list graph nodes")
    graph_node_list.add_argument("--node-type")
    graph_node_list.add_argument("--q")
    graph_node_list.add_argument("--page", type=int, default=1)
    graph_node_list.add_argument("--page-size", type=int, default=20)
    graph_node_list.set_defaults(handler=cmd_graph_nodes)
    graph_edge_list = graph_sub.add_parser("edges", help="list graph edges")
    graph_edge_list.add_argument("--relation-type")
    graph_edge_list.add_argument("--node-id")
    graph_edge_list.add_argument("--page", type=int, default=1)
    graph_edge_list.add_argument("--page-size", type=int, default=20)
    graph_edge_list.set_defaults(handler=cmd_graph_edges)

    request = sub.add_parser("request", help="raw HTTP escape hatch")
    request.add_argument(
        "method",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE", "get", "post", "put", "patch", "delete"],
    )
    request.add_argument("path", help="API path, for example /agent/capabilities")
    add_payload_flags(request, required=False)
    request.set_defaults(handler=cmd_request)

    db = sub.add_parser("db", help="show database access hints for agent operators")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_info = db_sub.add_parser("info", help="print psql and backup commands")
    db_info.set_defaults(handler=cmd_db_info)

    return parser


def extract_globals(argv: list[str]) -> tuple[dict[str, Any], list[str]]:
    values: dict[str, Any] = {"json": None, "base_url": None, "timeout": None, "sources": {}}
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--json":
            values["json"] = True
            values["sources"]["json"] = "flag"
            i += 1
            continue
        if token.startswith("--base-url="):
            values["base_url"] = token.split("=", 1)[1]
            values["sources"]["base_url"] = "flag"
            i += 1
            continue
        if token == "--base-url" and i + 1 < len(argv):
            values["base_url"] = argv[i + 1]
            values["sources"]["base_url"] = "flag"
            i += 2
            continue
        if token.startswith("--timeout="):
            values["timeout"] = parse_timeout_value(token.split("=", 1)[1])
            values["sources"]["timeout"] = "flag"
            i += 1
            continue
        if token == "--timeout" and i + 1 < len(argv):
            values["timeout"] = parse_timeout_value(argv[i + 1])
            values["sources"]["timeout"] = "flag"
            i += 2
            continue
        cleaned.append(token)
        i += 1

    if values["base_url"] is None:
        if os.getenv("SOLOCRM_BASE_URL"):
            values["sources"]["base_url"] = "env"
        else:
            values["sources"]["base_url"] = "default"
    if values["timeout"] is None:
        if os.getenv("SOLOCRM_TIMEOUT"):
            values["sources"]["timeout"] = "env"
        else:
            values["sources"]["timeout"] = "default"
    if values["json"] is None:
        values["sources"]["json"] = "default"
    return values, cleaned


def parse_timeout_value(raw: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise CliError(f"--timeout must be a number, got: {raw}", code="invalid_argument") from exc


def add_payload_flags(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--payload-json", help="JSON object payload")
    group.add_argument("--payload-file", help="path to JSON object payload")


def cmd_doctor(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "base_url": client.base_url,
        "timeout": client.timeout,
        "config": {
            "base_url_source": args.global_sources.get("base_url", "default"),
            "timeout_source": args.global_sources.get("timeout", "default"),
            "agent_name": os.getenv("SOLOCRM_AGENT_NAME", "cli"),
        },
        "checks": {},
    }
    try:
        health = client.request("GET", "/health")
        result["checks"]["health"] = {"ok": is_ok(health), "response": health}
    except CliError as exc:
        result["checks"]["health"] = {"ok": False, "error": error_payload(exc)}
        return result

    try:
        capabilities = client.request("GET", "/agent/capabilities")
        result["checks"]["capabilities"] = {
            "ok": is_ok(capabilities),
            "actions": sorted((capabilities.get("data") or {}).get("actions", {}).keys()),
        }
    except CliError as exc:
        result["checks"]["capabilities"] = {"ok": False, "error": error_payload(exc)}

    result["ok"] = all(check.get("ok") for check in result["checks"].values())
    return result


def cmd_capabilities(_args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", "/agent/capabilities"))


def cmd_summary(_args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", "/business/summary"))


def cmd_export(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    data = unwrap(client.request("GET", "/business/export"))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        out.write_text(f"{text}\n", encoding="utf-8")
        return {"file": str(out), "bytes": out.stat().st_size, "format": data.get("format")}
    return data


def cmd_action(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return run_agent_action(client, args.agent, args.action, read_payload(args))


def cmd_engagement_list(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/engagements",
            query={
                "stage": args.stage,
                "status": args.status,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    )


def cmd_engagement_get(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", f"/engagements/{args.engagement_id}"))


def cmd_engagement_create(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return run_agent_action(client, args.agent, "create_engagement", read_payload(args))


def cmd_engagement_update(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    payload = read_payload(args)
    payload["engagement_id"] = args.engagement_id
    return run_agent_action(client, args.agent, "update_engagement", payload)


def cmd_engagement_advance(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    payload: dict[str, Any] = {"engagement_id": args.engagement_id, "stage": args.stage}
    if args.status:
        payload["status"] = args.status
    if args.next_actions_json:
        payload["next_actions"] = parse_json(args.next_actions_json, "next-actions-json")
    if args.risks_json:
        payload["risks"] = parse_json(args.risks_json, "risks-json")
    return run_agent_action(client, args.agent, "advance_stage", payload)


def cmd_artifact_list(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/artifacts",
            query={"page": args.page, "page_size": args.page_size},
        )
    )


def cmd_artifact_get(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", f"/artifacts/{args.artifact_id}"))


def cmd_artifact_create(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return run_agent_action(client, args.agent, "add_artifact", read_payload(args))


def cmd_audit_list(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/agent/audit",
            query={
                "agent_name": args.agent_name,
                "action": args.action,
                "status": args.status,
                "target_type": args.target_type,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    )


def cmd_audit_errors(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/agent/audit",
            query={
                "agent_name": args.agent_name,
                "action": args.action,
                "status": "error",
                "target_type": args.target_type,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    )


def cmd_audit_get(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", f"/agent/audit/{args.audit_id}"))


def cmd_audit_summary(_args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(client.request("GET", "/agent/audit/summary"))


def cmd_graph_fact(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return run_agent_action(client, args.agent, "upsert_graph_fact", read_payload(args))


def cmd_graph_recall(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    payload = {
        "industry": args.industry,
        "customer": args.customer,
        "domain": args.domain,
        "project": args.project,
        "product": args.product,
        "city": args.city,
        "query": args.query,
        "include_artifacts": not args.no_artifacts,
        "limit": args.limit,
    }
    clean = {key: value for key, value in payload.items() if value is not None}
    return unwrap(client.request("POST", "/graph/recall", body=clean))


def cmd_graph_rebuild(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return run_agent_action(client, args.agent, "rebuild_graph", {})


def cmd_graph_nodes(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/graph/nodes",
            query={
                "node_type": args.node_type,
                "q": args.q,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    )


def cmd_graph_edges(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    return unwrap(
        client.request(
            "GET",
            "/graph/edges",
            query={
                "relation_type": args.relation_type,
                "node_id": args.node_id,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    )


def cmd_request(args: argparse.Namespace, client: ApiClient) -> dict[str, Any]:
    payload = read_json_body(args) if args.payload_json or args.payload_file else None
    return unwrap(client.request(args.method.upper(), args.path, body=payload))


def cmd_db_info(_args: argparse.Namespace, _client: ApiClient) -> dict[str, Any]:
    return {
        "policy": "Agents should use the SoloCRM HTTP API or CLI for normal reads/writes so audit logs are preserved.",
        "direct_database_use": "Use psql only for backups, restore drills, diagnostics, or explicit human-approved maintenance.",
        "docker_psql": "docker compose exec db psql -U ${POSTGRES_USER:-solocrm} -d ${POSTGRES_DB:-solocrm}",
        "docker_backup": "docker compose exec -T db pg_dump -U ${POSTGRES_USER:-solocrm} ${POSTGRES_DB:-solocrm} > backups/solocrm.sql",
        "tables": [
            "engagements",
            "business_artifacts",
            "agent_action_logs",
            "graph_nodes",
            "graph_edges",
            "customers",
            "success_cases",
            "visit_plans",
            "visit_records",
            "todos",
        ],
    }


def run_agent_action(
    client: ApiClient,
    agent_name: str,
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    body = {"agent_name": agent_name, "action": action, "payload": payload}
    return unwrap(client.request("POST", "/agent/actions", body=body))


def read_payload(args: argparse.Namespace) -> dict[str, Any]:
    body = read_json_body(args)
    if body is None:
        return {}
    return expect_object(body, "payload")


def read_json_body(args: argparse.Namespace) -> Any | None:
    if getattr(args, "payload_file", None):
        try:
            text = Path(args.payload_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise CliError(f"Cannot read payload file: {args.payload_file}", code="payload_file_error") from exc
        return parse_json(text, "payload-file")
    if getattr(args, "payload_json", None):
        return parse_json(args.payload_json, "payload-json")
    return None


def parse_json(value: str, label: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise CliError(f"{label} must be valid JSON: {exc.msg}", code="invalid_payload") from exc


def expect_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CliError(f"{label} must be a JSON object", code="invalid_payload")
    return value


def unwrap(response: dict[str, Any]) -> Any:
    if response.get("code", 0) != 0:
        raise CliError(response.get("message", "SoloCRM API returned an error"), code="api_error", details=response)
    return response.get("data")


def is_ok(response: dict[str, Any]) -> bool:
    return response.get("code", 0) == 0


def emit(result: Any, *, json_mode: bool, ok: bool = True) -> None:
    if json_mode:
        print(json.dumps({"ok": ok, "data": result}, ensure_ascii=False, indent=2))
        return
    if isinstance(result, (dict, list)):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)


def emit_error(exc: CliError, *, json_mode: bool) -> None:
    payload = {"ok": False, "error": error_payload(exc)}
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Error: {exc.message}", file=sys.stderr)


def error_payload(exc: CliError) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details is not None:
        payload["details"] = exc.details
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
