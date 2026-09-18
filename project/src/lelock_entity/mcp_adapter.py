"""Optional official Python SDK adapter. Requires separately installed/tested `mcp` package.
Only the agent token is loaded; no operator approvals or policy-changing tools are exposed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from .client import Client
from .common import canonical, strict_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-credentials", type=Path, required=True)
    args = parser.parse_args()
    credentials = strict_json(args.agent_credentials.read_bytes())
    client = Client(credentials["base_url"], credentials["agent_token"])
    try:
        from importlib.metadata import version
        if version("mcp").split(".")[0] != "2":
            raise ImportError("This adapter targets official MCP Python SDK 2.x")
        from mcp.server import MCPServer
    except ImportError as exc:
        raise SystemExit("Install and verify the official MCP Python SDK 2.x in an isolated environment first.") from exc
    mcp = MCPServer("Lelock Entity")

    @mcp.tool()
    def lelock_status() -> str:
        """Inspect the paired local entity. This is not a promise of model-independent behavior."""
        return canonical(client.request("/v1/status"))

    @mcp.tool()
    def lelock_tools() -> str:
        """List the current session's actually enabled tools and input schemas."""
        return canonical(client.request("/v1/tools"))

    @mcp.tool()
    def lelock_call(tool: str, arguments_json: str, request_id: str) -> str:
        """Invoke an enabled tool using its listed schema. Use a stable request ID for retries.
        A pending action requires a separate operator approval, never an agent self-approval.
        """
        return canonical(client.invoke(tool, strict_json(arguments_json), request_id=request_id))

    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
