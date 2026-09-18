"""Client for the local Entity bridge. No redirects, ambient proxies, or public HTTP transport."""
from __future__ import annotations
import urllib.request
import urllib.error
from urllib.parse import urlsplit
import uuid
from .common import EntityError, canonical, strict_json

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise EntityError("Bridge redirect refused")

class Client:
    def __init__(self, base_url: str, token: str):
        parsed = urlsplit(base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise EntityError("This client supports local loopback HTTP only")
        if parsed.port is None or len(token) < 32:
            raise EntityError("Expected explicit port and strong token")
        self.base_url, self.token = base_url, token
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path: str, data: dict | None = None):
        if not path.startswith("/v1/") or "?" in path or "#" in path:
            raise EntityError("Invalid bridge path")
        headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
        request = urllib.request.Request(self.base_url + path,
                  data=None if data is None else canonical(data).encode(), headers=headers)
        try:
            with self.opener.open(request, timeout=180) as response:
                raw = response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            raw = exc.read(2_000_001)
            raise EntityError("Bridge request rejected: " + canonical(strict_json(raw))) from exc
        return strict_json(raw)

    def invoke(self, tool: str, arguments: dict, *, request_id: str | None = None):
        return self.request("/v1/invoke", {"tool": tool, "arguments_json": canonical(arguments),
                                          "request_id": request_id or uuid.uuid4().hex})
