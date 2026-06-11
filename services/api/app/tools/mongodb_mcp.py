from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.db.mongo import BaseRepository
from app.tools.policies import guard_read


@dataclass
class ToolTrace:
    steps: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        *,
        tool: str,
        collection: str,
        purpose: str,
        status: str,
        duration_ms: int,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
        transport: str = "mcp_trace_bridge",
    ) -> None:
        self.steps.append(
            {
                "tool": tool,
                "collection": collection,
                "purpose": purpose,
                "status": status,
                "duration_ms": duration_ms,
                "transport": transport,
                "input": input_summary or {},
                "output": output_summary or {},
                "evidence_ids": evidence_ids or [],
            }
        )


class MongoMCPBridge:
    """MongoDB MCP Server database tool surface with deterministic fallback.

    Hosted runs launch the official MongoDB MCP Server and record its transport
    in the visible tool trace. The local fallback keeps the same tool names and
    guardrails while executing against the repository abstraction, so every agent
    run remains reproducible without requiring secrets.
    """

    def __init__(self, repo: BaseRepository, trace: ToolTrace):
        self.repo = repo
        self.trace = trace
        self.real_client = RealMongoMCPClient() if settings.use_real_mcp and settings.mdb_mcp_connection_string else None

    def collection_schema(self, collection: str, purpose: str) -> dict[str, Any]:
        start = time.perf_counter()
        decision = guard_read(collection, limit=20)
        if not decision.allowed:
            result = {"error": decision.reason}
            status = "blocked"
        else:
            result = self.repo.collection_schema(collection)
            status = "ok"
        transport, mcp_error = self._try_real_tool_call(
            "collection-schema",
            {"database": settings.mongodb_db, "collection": collection},
        )
        if mcp_error:
            status = "fallback"
        self.trace.add(
            tool="mongodb.collection-schema",
            collection=collection,
            purpose=purpose,
            status=status,
            duration_ms=int((time.perf_counter() - start) * 1000),
            output_summary={
                "fields": list(result.get("fields", {}).keys()) if isinstance(result, dict) else [],
                **({"mcp_error": mcp_error} if mcp_error else {}),
            },
            transport=transport,
        )
        return result

    def find(self, collection: str, query: dict[str, Any] | None, purpose: str, limit: int = 20) -> list[dict[str, Any]]:
        start = time.perf_counter()
        decision = guard_read(collection, limit=limit)
        if not decision.allowed:
            rows: list[dict[str, Any]] = []
            status = "blocked"
        else:
            rows = self.repo.find(collection, query=query, limit=limit)
            status = "ok"
        transport, mcp_error = self._try_real_tool_call(
            "find",
            {"database": settings.mongodb_db, "collection": collection, "filter": query or {}, "limit": limit},
        )
        if mcp_error:
            status = "fallback"
        self.trace.add(
            tool="mongodb.find",
            collection=collection,
            purpose=purpose,
            status=status,
            duration_ms=int((time.perf_counter() - start) * 1000),
            input_summary={"query": query or {}, "limit": limit},
            output_summary={"row_count": len(rows), **({"mcp_error": mcp_error} if mcp_error else {})},
            evidence_ids=[str(row.get("_id")) for row in rows[:8]],
            transport=transport,
        )
        return rows

    def aggregate(self, collection: str, pipeline: list[dict[str, Any]], purpose: str) -> list[dict[str, Any]]:
        start = time.perf_counter()
        decision = guard_read(collection)
        repo_error: str | None = None
        if not decision.allowed:
            rows: list[dict[str, Any]] = []
            status = "blocked"
        else:
            try:
                rows = self.repo.aggregate(collection, pipeline)
                status = "ok"
            except Exception as exc:
                rows = []
                status = "fallback"
                repo_error = f"{type(exc).__name__}: {exc}"
        transport, mcp_error = self._try_real_tool_call(
            "aggregate",
            {"database": settings.mongodb_db, "collection": collection, "pipeline": pipeline},
        )
        if mcp_error:
            status = "fallback"
        self.trace.add(
            tool="mongodb.aggregate",
            collection=collection,
            purpose=purpose,
            status=status,
            duration_ms=int((time.perf_counter() - start) * 1000),
            input_summary={"pipeline": pipeline[:4]},
            output_summary={
                "row_count": len(rows),
                **({"repo_error": repo_error} if repo_error else {}),
                **({"mcp_error": mcp_error} if mcp_error else {}),
            },
            evidence_ids=[str(row.get("_id")) for row in rows[:8]],
            transport=transport,
        )
        return rows

    def count(self, collection: str, query: dict[str, Any] | None, purpose: str) -> int:
        start = time.perf_counter()
        decision = guard_read(collection)
        if not decision.allowed:
            count = 0
            status = "blocked"
        else:
            count = self.repo.count(collection, query=query)
            status = "ok"
        transport, mcp_error = self._try_real_tool_call(
            "count",
            {"database": settings.mongodb_db, "collection": collection, "query": query or {}},
        )
        if mcp_error:
            status = "fallback"
        self.trace.add(
            tool="mongodb.count",
            collection=collection,
            purpose=purpose,
            status=status,
            duration_ms=int((time.perf_counter() - start) * 1000),
            input_summary={"query": query or {}},
            output_summary={"count": count, **({"mcp_error": mcp_error} if mcp_error else {})},
            transport=transport,
        )
        return count

    def _try_real_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> tuple[str, str | None]:
        if not self.real_client:
            return "mcp_trace_bridge", None
        try:
            self.real_client.call_tool(tool_name, arguments)
            return "mongodb-mcp-server", None
        except TimeoutError as exc:
            try:
                self.real_client.call_tool(tool_name, arguments)
                return "mongodb-mcp-server", None
            except Exception as retry_exc:
                return "mcp_trace_bridge", f"{exc}; retry failed: {retry_exc}"
        except Exception as exc:
            return "mcp_trace_bridge", str(exc)

    def close(self) -> None:
        if self.real_client:
            self.real_client.close()


class RealMongoMCPClient:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.next_id = 1

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self._ensure_started()
        return self._request("tools/call", {"name": name, "arguments": arguments}, timeout_s=45)

    def _ensure_started(self) -> None:
        if self.process and self.process.poll() is None:
            return
        env = os.environ.copy()
        env.setdefault("MDB_MCP_CONNECTION_STRING", settings.mdb_mcp_connection_string or "")
        env.setdefault("MDB_MCP_READ_ONLY", "true")
        command = ["mongodb-mcp-server"] if shutil.which("mongodb-mcp-server") else ["npx", "-y", "mongodb-mcp-server@latest"]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        try:
            self._request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "venueops-agent", "version": "0.1.0"},
                },
                timeout_s=30,
            )
            self._notify("notifications/initialized", {})
        except Exception:
            self.close()
            raise

    def _request(self, method: str, params: dict[str, Any], timeout_s: int) -> Any:
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MongoDB MCP process is not running")
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            line = self._read_stdout_line(max(deadline - time.time(), 0.1))
            if not line:
                continue
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(message["error"])
            return message.get("result")
        raise TimeoutError(f"Timed out waiting for MongoDB MCP response to {method}")

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            return
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.process.stdin.flush()

    def _read_stdout_line(self, timeout_s: float) -> str | None:
        if not self.process or not self.process.stdout:
            return None
        selector = selectors.DefaultSelector()
        selector.register(self.process.stdout, selectors.EVENT_READ)
        try:
            events = selector.select(timeout_s)
            if not events:
                return None
            return self.process.stdout.readline()
        finally:
            selector.close()

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self.process = None
