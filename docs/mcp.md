# MCP server

Stdio JSON-RPC 2.0 (`mcp/server.py`). No extra pip packages.

## Tools

| Tool | Gateway | Notes |
|------|---------|-------|
| cortex_web_search | api-v2 `/v1/web/search` | 5000/day |
| cortex_quota | me/usage on each host | no generation |
| cortex_catalog | GET `/v1/models` | no key on most |
| cortex_image | core `seedream-5` or studio `gpt-image-2` | saves under `cortex-out/` |
| cortex_video | core `minimax-h3` | 4–15 s, minutes |
| cortex_speech | core `speech-2-8-hd` | default Turkish voice |
| cortex_music | core `music-3` or studio v1 | |
| cortex_voices | core `/v1/voices` | no quota |
| cortex_upload | core `/v1/uploads` | 6 h public URL |
| cortex_job | core `/v1/jobs/:id` | poll |
| cortex_chat | any text gateway | one-shot, does not switch session |

## OpenCode

```json
"mcp": {
  "servers": {
    "cortex": {
      "type": "local",
      "command": ["python", "mcp/server.py"],
      "codemode": false
    }
  }
}
```

Windows: `mcp/run.cmd` so `cortex.env` is loaded.

## Claude Code

```json
"cortex": {
  "type": "stdio",
  "command": "cmd",
  "args": ["/c", "C:\\path\\to\\cortex-hub\\mcp\\run.cmd"]
}
```

## Smoke

```bash
python mcp/smoke.py
```

Does not spend image/video quota.
