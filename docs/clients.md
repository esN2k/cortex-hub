# Client setup

One key. Paste the matching snippet. Full UI copy lives in Hub → User guide.

## OpenCode

1. `scripts/install.ps1` or copy `config/opencode.json` → `~/.config/opencode/opencode.json`
2. `cortex.env` next to it or `CORTEX_API_KEY` in the user environment
3. Restart OpenCode. Default model: `grok/grok-4.6-max`
4. MCP: `mcp/run.cmd` (Windows) or `python mcp/server.py`

Grok 401/403/408/429/5xx → plugin switches the session to Sonnet thinking.

## Claude Code CLI

Merge `examples/claude-code.env.json` into `~/.claude/settings.json`.

```json
"env": {
  "ANTHROPIC_BASE_URL": "https://app.claude.gg",
  "ANTHROPIC_AUTH_TOKEN": "sk-..."
}
```

MCP: `~/.claude.json` → `mcpServers.cortex` command = `mcp/run.cmd`.

## Claude Desktop / Cowork

1. Help → Troubleshooting → Enable Developer Mode (app restarts)
2. Developer → Configure Third-Party Inference
3. Gateway `https://app.claude.gg`, bearer, model `claude-sonnet-4-6-thinking`
4. Apply locally

## Cline

Provider **Anthropic**, custom base URL `https://app.claude.gg`, model `claude-sonnet-4-6-thinking`.  
For Grok: OpenAI Compatible, `https://grok-beta-v4.claude.gg/v1`, `grok-4.6-max`.

See `examples/cline-anthropic.json`.

## Roo / Zoo Code

OpenAI Compatible, base `https://grok-beta-v4.claude.gg/v1`, model `grok-4.6-max`.

## cursor-byok / Cursor Assistant

Import `examples/cursor-byok-preset.json`. Paste your key in the app. This repo does not MITM Cursor.

## TRAE

Settings → Models → Custom Config → Anthropic Messages, Full URL on, `https://app.claude.gg`, model `claude-sonnet-4-6-thinking`.
