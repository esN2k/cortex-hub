---
name: cortex
description: CortexAI tools — image, video, speech, music, SFX, search, jury, embeddings, quota. Use when the user wants media, a second-model review, current web facts, or semantic embeddings.
---

# Cortex tools (MCP v1.1)

Brain: `grok/grok-4.6-max`. Fallback: `app-cortex/claude-sonnet-4-6-thinking`. Media and extra models are **tools**.

## Do this

- Stills → `cortex_enhance_prompt` then `cortex_image` (`seedream-5-pro` or studio `gemini-3-pro-image` for readable text). Pass `image_urls` for consistency.
- Edit existing → `cortex_edit` (`remove-bg` / `upscale` / `edit`).
- Video → still first, then `cortex_video` model `wan-2-6` + `reference_images`, or H3 + `first_frame`.
- Speech → `cortex_voices` then `cortex_speech` (Turkish default). One-off identity: `cortex_voice_design` / `cortex_voice_clone`.
- Music → `cortex_music` backend `core`. Lyrics: `cortex_lyrics` then music.
- SFX → `cortex_sfx`.
- Facts → `cortex_web_search` then `cortex_fetch` on the URL.
- Hard call → `cortex_jury` (Grok + Sonnet + Ox in parallel).
- Notes search → `cortex_embed`.
- 503 / mystery params → `cortex_status` / `cortex_model_schema`.
- Quota before a media burst → `cortex_quota`.

Output: `cortex-out/` (3 h on the server — files are saved locally).

Do **not** burn app.claude.gg 2500 on jury/embeddings; those buckets are `api` / `llm` / `grok`.
