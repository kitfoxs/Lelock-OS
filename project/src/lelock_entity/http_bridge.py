"""Loopback-only JSON bridge with distinct agent/operator credentials. Not a public Web server."""
from __future__ import annotations
import hmac
import http.server
import json
import secrets
import threading
import time
from urllib.parse import urlsplit
from .common import EntityError, canonical, strict_json, object_schema, validate, STRING
from .core import EntityCore

class Bridge:
    def __init__(self, core: EntityCore, *, port: int = 0, origins: tuple[str, ...] = (),
                 agent_token: str | None = None, operator_token: str | None = None):
        self.core = core
        self.agent_token = agent_token or secrets.token_urlsafe(32)
        self.operator_token = operator_token or secrets.token_urlsafe(32)
        if min(len(self.agent_token), len(self.operator_token)) < 32 or self.agent_token == self.operator_token:
            raise EntityError("Independent strong agent/operator tokens required")
        for origin in origins:
            parsed = urlsplit(origin)
            if origin in {"*", "null"} or not parsed.scheme or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
                raise EntityError("Origin must be an exact scheme://authority, never wildcard/null")
        self.origins = frozenset(origins)
        outer = self
        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            server_version = "LelockEntity/0.2"
            sys_version = ""

            def setup(self):
                super().setup()
                self.connection.settimeout(5)

            def log_message(self, *_):
                pass

            def respond(self, status: int, value: dict):
                raw = canonical(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Connection", "close")
                origin = self.headers.get("Origin")
                if origin in outer.origins:
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")
                    self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.end_headers()
                self.wfile.write(raw)
                self.close_connection = True

            def boundary(self) -> bool:
                hosts = self.headers.get_all("Host", [])
                origins = self.headers.get_all("Origin", [])
                allowed_hosts = {f"127.0.0.1:{outer.port}", f"localhost:{outer.port}"}
                if len(hosts) != 1 or hosts[0] not in allowed_hosts:
                    self.respond(403, {"error": "host_rejected"})
                    return False
                if len(origins) > 1 or (origins and origins[0] not in outer.origins):
                    self.respond(403, {"error": "origin_rejected"})
                    return False
                if "?" in self.path or "#" in self.path or self.headers.get("Transfer-Encoding"):
                    self.respond(400, {"error": "unsupported_request_shape"})
                    return False
                return True

            def authenticate(self, operator: bool = False) -> bool:
                values = self.headers.get_all("Authorization", [])
                if len(values) != 1 or not values[0].startswith("Bearer "):
                    self.respond(401, {"error": "authentication_required"})
                    return False
                if time.time() >= outer.core.session.expires_at and self.path != "/v1/operator/stop":
                    self.respond(403, {"error": "session_expired"})
                    return False
                token = values[0][7:]
                if not token.isascii() or len(token) > 256:
                    self.respond(403, {"error": "invalid_token_shape"})
                    return False
                valid_operator = hmac.compare_digest(token, outer.operator_token)
                valid_agent = hmac.compare_digest(token, outer.agent_token)
                if not valid_operator and (operator or not valid_agent):
                    self.respond(403, {"error": "role_rejected"})
                    return False
                return True

            def body(self):
                lengths = self.headers.get_all("Content-Length", [])
                content_types = self.headers.get_all("Content-Type", [])
                if len(lengths) != 1 or len(content_types) != 1 or content_types[0].split(";")[0].strip().lower() != "application/json":
                    raise EntityError("Expected one Content-Length and application/json")
                try:
                    length = int(lengths[0])
                except ValueError as exc:
                    raise EntityError("Invalid content length") from exc
                if not 0 < length <= 2_000_000:
                    raise EntityError("Body length outside bounds")
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise EntityError("Incomplete body")
                value = strict_json(raw)
                if not isinstance(value, dict):
                    raise EntityError("Body must be a JSON object")
                return value

            def do_OPTIONS(self):
                # A valid preflight reveals no authenticated data or write capability.
                if self.boundary():
                    self.respond(200, {"status": "preflight"})

            def do_GET(self):
                if not self.boundary() or not self.authenticate(operator=self.path.startswith("/v1/operator/")):
                    return
                if self.path == "/v1/status":
                    self.respond(200, outer.core.status())
                elif self.path == "/v1/tools":
                    self.respond(200, {"tools": outer.core.schemas()})
                elif self.path == "/v1/operator/actions":
                    self.respond(200, {"actions": outer.core.store.pending(outer.core.session.entity, outer.core.session.ident)})
                else:
                    self.respond(404, {"error": "route_not_found"})

            def do_POST(self):
                operator = self.path.startswith("/v1/operator/")
                if not self.boundary() or not self.authenticate(operator=operator):
                    return
                try:
                    data = self.body()
                    if self.path == "/v1/invoke":
                        validate(object_schema({"tool": STRING,
                            "arguments_json": {"type": "string", "maxLength": 1_000_000},
                            "request_id": {"type": "string", "minLength": 1, "maxLength": 150}},
                            ["tool", "arguments_json", "request_id"]), data)
                        args = strict_json(data["arguments_json"])
                        result = outer.core.invoke(data["tool"], args, request_id=data["request_id"])
                    elif self.path == "/v1/operator/approve":
                        validate(object_schema({"action_id": STRING, "digest": STRING}, ["action_id", "digest"]), data)
                        result = outer.core.approve(data["action_id"], data["digest"])
                    elif self.path == "/v1/operator/reject":
                        validate(object_schema({"action_id": STRING}, ["action_id"]), data)
                        result = outer.core.reject(data["action_id"])
                    elif self.path == "/v1/operator/stop":
                        validate(object_schema({}), data)
                        outer.core.stop.stop()
                        result = {"status": "stopped"}
                    else:
                        self.respond(404, {"error": "route_not_found"})
                        return
                    self.respond(200, result)
                except EntityError as exc:
                    self.respond(409, {"error": "refused_or_failed", "message": str(exc)})
                except Exception:
                    self.respond(500, {"error": "internal_failure_no_success_claimed"})

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = None

    def start(self):
        if self.thread is not None:
            raise EntityError("Bridge already started")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def close(self):
        if self.thread is not None:
            self.server.shutdown()
            self.thread.join(timeout=3)
        self.server.server_close()

    def credentials(self) -> dict:
        """Operator delivery only. Never include this object in a prompt, receipt or public file."""
        return {"base_url": f"http://127.0.0.1:{self.port}", "agent_token": self.agent_token,
                "operator_token": self.operator_token, "session": self.core.session.ident}
