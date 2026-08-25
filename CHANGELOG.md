# Changelog

## 0.2.0 — 2026-08-25

- MCP **22 tools** (was 11): fetch, status, model schema, prompt enhance, image refs + Midjourney params, edit (remove-bg/upscale), video omni-ref + wan-2-6, lyrics, SFX, voice-design/clone, jury, embeddings
- Local paths in `image_urls` / `reference_*` / `first_frame` auto-upload to core (6 h URL)
- Default music backend is core `music-3` (studio v1 often 400)
- `scripts/mcp_handshake.py`, `scripts/smoke_v11.py`

## 0.1.0 — 2026-08-25

- Local Hub on `127.0.0.1:3848`: quota, live catalog, model probe, setup snippets, studio, bug-report markdown
- MCP stdio: search, quota, catalog, image, video, speech, music, voices, upload, job, chat
- OpenCode plugins: api-v2 web search, Grok → Sonnet thinking fallback
- Presets: Cline, Claude Code, cursor-byok
- Probe snapshot: 4/7 models live (Kimi 402, Laguna/Kimi 503 documented)
- Dogfood media via core.claude.gg: hero stills, 5 s trailer, TTS, theme bed
