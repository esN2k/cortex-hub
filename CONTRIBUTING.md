# Contributing

## Scope

This project is a **local helper** for CortexAI subscribers: catalog, probe, setup snippets, MCP, bug-report markdown.

Out of scope:

- Sharing one API key across users
- Reverse-engineering Cursor’s private protocol
- Inventing FOGRA / exam questions (unrelated)

## How to work

1. Fork, branch from `main`.
2. No secrets in commits (`cortex.env`, `sk-`).
3. Python 3.10+, stdlib only for `hub/` and `mcp/`.
4. Probe failures (402/503) are data, not always a code bug — attach Hub report markdown.

```bash
python mcp/smoke.py
python -m py_compile hub/server.py mcp/server.py mcp/client.py
```

## PRs

- One concern per PR
- Update `docs/` if you add a gateway or client
- Screenshots: no live keys in the frame
