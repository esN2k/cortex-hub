#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP initialize + tools/list. No network generation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
proc = subprocess.Popen(
    [sys.executable, str(root / "mcp" / "server.py")],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=str(root),
)
assert proc.stdin and proc.stdout
msgs = [
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "handshake", "version": "0"},
        },
    },
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
]
for m in msgs:
    proc.stdin.write((json.dumps(m) + "\n").encode("utf-8"))
proc.stdin.flush()
proc.stdin.close()
out_b, err_b = proc.communicate(timeout=20)
out = (out_b or b"").decode("utf-8", errors="replace")
err = (err_b or b"").decode("utf-8", errors="replace")
lines = [ln for ln in out.splitlines() if ln.strip()]
print("STDERR", err[:400])
print("N_REPLIES", len(lines))
n_tools = 0
for ln in lines:
    obj = json.loads(ln)
    if obj.get("id") == 1:
        print("INIT", obj.get("result", {}).get("serverInfo"))
    if obj.get("id") == 2:
        tools = (obj.get("result") or {}).get("tools") or []
        n_tools = len(tools)
        print("TOOLS", n_tools)
        print("\n".join(t.get("name") or "" for t in tools))
sys.exit(0 if n_tools >= 22 else 1)
