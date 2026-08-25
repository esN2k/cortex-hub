# MCP server

Stdio JSON-RPC 2.0 (`mcp/server.py`). No extra pip packages. **v1.1 — 22 tools.**

## Tools

| Tool | Gateway | Notes |
|------|---------|-------|
| cortex_web_search | api-v2 `/v1/web/search` | 5000/day |
| cortex_fetch | any http(s) | strip HTML after search |
| cortex_quota | me/usage | no generation |
| cortex_status | studio+core `/v1/status` | no key; check before 503 retry |
| cortex_catalog | GET `/v1/models` | live IDs |
| cortex_model_schema | GET `/v1/models/:id` | full params + example |
| cortex_enhance_prompt | studio `/v1/prompts/enhance` | **helper bucket, not daily media** |
| cortex_image | core / studio | `image_urls` (path or URL), Midjourney stylize/chaos/weird |
| cortex_edit | core | `remove-bg`, `upscale`, or prompt-edit (`nano-banana-2`) |
| cortex_video | core | H3, wan-2-6 (still→video), first/last frame, omni refs |
| cortex_speech | core `speech-2-8-hd` | Turkish default, optional subtitles |
| cortex_music | core `music-3` (default) | studio v1 may 400 |
| cortex_lyrics | studio lyrics enhance + tokenize | helper quota |
| cortex_sfx | studio `audio/generate` tool=sfx | UI / whoosh |
| cortex_voices | core `/v1/voices` | no quota |
| cortex_voice_design | core `voice-design` | persistent `voice_id` |
| cortex_voice_clone | core `voice-clone` | local file or URL |
| cortex_upload | core `/v1/uploads` | 6 h public URL |
| cortex_job | core `/v1/jobs/:id` | poll |
| cortex_chat | text gateways | one-shot second opinion |
| cortex_jury | grok + app + api-v2 parallel | default Grok Max, Sonnet thinking, Ox Alpha |
| cortex_embed | api `text-embedding-3-small` | notes / semantic search; **live catalog lists the model — POST may 502** (same class as Kimi 402) |

## Quality path

1. `cortex_status` if yesterday’s probe was 503  
2. `cortex_enhance_prompt` before stills (free helper)  
3. `cortex_image` with `image_urls` for character/UI lock  
4. `cortex_video` `wan-2-6` + that still, or H3 + `first_frame`  
5. `cortex_speech` same `voice_id`; optional `cortex_voice_design` once  
6. Hard review: `cortex_jury` (uses **api/llm/grok** buckets, not the session)

Local paths in `image_urls` / `reference_*` / `first_frame` are uploaded automatically.

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
python scripts/mcp_handshake.py
```

`smoke.py` does not spend image/video quota.
