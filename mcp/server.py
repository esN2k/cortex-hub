# -*- coding: utf-8 -*-
"""CortexAI MCP (stdio JSON-RPC 2.0) — studio / core / search / jury / media pipeline."""
from __future__ import annotations

import json
import sys
from typing import Any

from client import (
    catalog,
    chat,
    core_generate,
    dump,
    embed,
    enhance_prompt,
    fetch_url,
    gateway_status,
    jury,
    load_key,
    lyrics_enhance,
    lyrics_tokenize,
    model_schema,
    poll_core_job,
    quota,
    resolve_ref,
    resolve_refs,
    studio_image,
    studio_music,
    studio_sfx,
    upload,
    voices,
    web_search,
)

PROTOCOL = "2024-11-05"


def _ok(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _text(obj: Any) -> dict[str, Any]:
    if isinstance(obj, str):
        body = obj
    else:
        body = dump(obj)
    return {"content": [{"type": "text", "text": body}]}


def _str_list(val: Any) -> list[str] | None:
    if val is None:
        return None
    if isinstance(val, str):
        return [val] if val.strip() else None
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    return None


TOOLS: list[dict[str, Any]] = [
    {
        "name": "cortex_web_search",
        "description": (
            "Web search via api-v2.claude.gg (5000/day). "
            "Use for current facts, news, docs. Returns titles/snippets/urls."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "num_results": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_fetch",
        "description": "Fetch a public http(s) URL and return stripped text (after web_search).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_bytes": {"type": "integer", "default": 200000},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_quota",
        "description": "Remaining daily quota across claude.gg / app / api / llm / studio / core.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "cortex_status",
        "description": "Live studio+core status (no quota). Check before retrying 503.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "cortex_catalog",
        "description": "List live model IDs on a Cortex gateway (or all).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "which": {
                    "type": "string",
                    "enum": [
                        "all",
                        "app",
                        "claude",
                        "api",
                        "llm",
                        "llm-v2",
                        "api-v2",
                        "grok",
                        "studio",
                        "core",
                    ],
                    "default": "all",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_model_schema",
        "description": "GET /v1/models/:id — full parameter schema + example (core or studio).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "backend": {"type": "string", "enum": ["core", "studio"], "default": "core"},
                "model": {"type": "string"},
            },
            "required": ["model"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_enhance_prompt",
        "description": (
            "Studio prompt enhance (helper bucket — NOT daily media quota). "
            "Call before cortex_image for quality."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "model": {"type": "string", "description": "optional catalog id e.g. gpt-image-2"},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_image",
        "description": (
            "Generate an image. backend=core (default seedream-5 / seedream-5-pro) "
            "or studio (gpt-image-2, gemini-3-pro-image, …). "
            "image_urls: local paths or http URLs (uploaded if local). "
            "Midjourney: stylize/chaos/weird. Files in cortex-out/."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "backend": {"type": "string", "enum": ["core", "studio"], "default": "core"},
                "model": {"type": "string"},
                "aspect_ratio": {"type": "string"},
                "quality": {"type": "string", "enum": ["low", "medium", "high"]},
                "resolution": {"type": "string"},
                "size": {"type": "string", "description": "gpt-image size e.g. 2K"},
                "image_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "reference images (path or URL)",
                },
                "seed": {"type": "integer"},
                "stylize": {"type": "integer"},
                "chaos": {"type": "integer"},
                "weird": {"type": "integer"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_edit",
        "description": (
            "Edit an existing image via core: remove-bg, upscale, or prompt-edit "
            "(nano-banana-2 / flux-kontext / seedream with image_urls)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "local path or URL"},
                "op": {
                    "type": "string",
                    "enum": ["remove-bg", "upscale", "edit"],
                    "default": "edit",
                },
                "prompt": {"type": "string"},
                "model": {"type": "string", "description": "for op=edit, default nano-banana-2"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["image"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_video",
        "description": (
            "Generate video via core. Default minimax-h3. "
            "Quality path: still image then wan-2-6 (image-to-video) or H3 + first_frame. "
            "Refs: local paths uploaded automatically. duration 4-15s (model-dependent)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "model": {"type": "string", "default": "minimax-h3"},
                "duration": {"type": "integer", "default": 5},
                "resolution": {"type": "string", "default": "768P"},
                "ratio": {"type": "string"},
                "generate_audio": {"type": "boolean", "default": False},
                "reference_images": {"type": "array", "items": {"type": "string"}},
                "reference_videos": {"type": "array", "items": {"type": "string"}},
                "reference_audios": {"type": "array", "items": {"type": "string"}},
                "first_frame": {"type": "string"},
                "last_frame": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_speech",
        "description": "TTS via core speech-2-8-hd. Default Turkish energetic voice. Optional subtitles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "voice_id": {"type": "string", "default": "Turkish_Energetic_Speaker_v3"},
                "language": {"type": "string", "default": "Turkish"},
                "emotion": {"type": "string"},
                "speed": {"type": "number"},
                "subtitles": {"type": "boolean", "default": True},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_music",
        "description": "Generate music. Prefer backend=core (music-3). studio v1 may 400.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "style / mood"},
                "backend": {"type": "string", "enum": ["studio", "core"], "default": "core"},
                "instrumental": {"type": "boolean", "default": True},
                "lyrics": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_lyrics",
        "description": "Studio lyricist (helper quota). Expand idea+style; optional tokenize (1531 BPE cap).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idea": {"type": "string"},
                "style": {"type": "string"},
                "language": {"type": "string", "default": "tr"},
                "tokenize": {"type": "boolean", "default": True},
            },
            "required": ["idea"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_sfx",
        "description": "Studio sound effect (tool=sfx). UI clicks, whooshes. Counts toward studio daily.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "duration_seconds": {"type": "number"},
                "loop": {"type": "boolean", "default": False},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_voices",
        "description": "List GateAI Core TTS voices (no quota). language=turkish recommended.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "default": "turkish"},
                "limit": {"type": "integer", "default": 20},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_voice_design",
        "description": "Create a persistent core voice_id from a text description; use later in cortex_speech.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "gender, age, tone, accent"},
                "preview_text": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_voice_clone",
        "description": "Clone a voice from a local audio file or URL (several seconds of speech). Returns voice_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio": {"type": "string", "description": "path or URL"},
                "preview_text": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["audio"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_upload",
        "description": "Upload a local file to core.claude.gg; returns absolute_url for image/video refs (6h).",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_job",
        "description": "Poll a core.claude.gg job by id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "wait": {"type": "boolean", "default": False},
            },
            "required": ["job_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_chat",
        "description": (
            "One-shot chat on a Cortex text gateway (does not switch the OpenCode session model). "
            "Use for a second opinion. gateway: app|claude|api|llm|llm-v2|api-v2|grok"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "gateway": {
                    "type": "string",
                    "enum": ["app", "claude", "api", "llm", "llm-v2", "api-v2", "grok"],
                    "default": "api-v2",
                },
                "model": {"type": "string"},
                "prompt": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 1024},
            },
            "required": ["model", "prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_jury",
        "description": (
            "Parallel second opinions (default Grok Max + Sonnet thinking + Ox Alpha). "
            "Uses api/llm/grok/app buckets — not the session model."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 800},
                "system": {"type": "string"},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_embed",
        "description": "Embeddings via api.claude.gg text-embedding-3-small (notes / semantic search).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texts": {"type": "array", "items": {"type": "string"}},
                "model": {"type": "string", "default": "text-embedding-3-small"},
            },
            "required": ["texts"],
            "additionalProperties": False,
        },
    },
]


def _image_core(args: dict[str, Any]) -> dict[str, Any]:
    prompt = str(args["prompt"])
    wait = bool(args.get("wait", True))
    payload: dict[str, Any] = {
        "prompt": prompt,
        "model": args.get("model") or "seedream-5",
    }
    if args.get("aspect_ratio"):
        payload["aspectRatio"] = args["aspect_ratio"]
    if args.get("size"):
        payload["size"] = args["size"]
    if args.get("seed") is not None:
        payload["seed"] = int(args["seed"])
    refs = resolve_refs(_str_list(args.get("image_urls")))
    if refs:
        payload["imageUrls"] = refs
    if args.get("stylize") is not None:
        payload["stylize"] = int(args["stylize"])
    if args.get("chaos") is not None:
        payload["chaos"] = int(args["chaos"])
    if args.get("weird") is not None:
        payload["weird"] = int(args["weird"])
    return core_generate("image", payload, wait=wait)


def _image_studio(args: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": str(args["prompt"]),
        "model": args.get("model") or "gpt-image-2",
    }
    if args.get("aspect_ratio"):
        payload["aspect_ratio"] = args["aspect_ratio"]
    if args.get("quality"):
        payload["quality"] = args["quality"]
    if args.get("resolution"):
        payload["resolution"] = args["resolution"]
    return studio_image(payload, wait=bool(args.get("wait", True)))


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "cortex_web_search":
        return _text(web_search(str(args["query"]), int(args.get("num_results") or 5)))
    if name == "cortex_fetch":
        return _text(fetch_url(str(args["url"]), int(args.get("max_bytes") or 200000)))
    if name == "cortex_quota":
        return _text(quota())
    if name == "cortex_status":
        return _text(gateway_status())
    if name == "cortex_catalog":
        return _text(catalog(str(args.get("which") or "all")))
    if name == "cortex_model_schema":
        return _text(model_schema(str(args.get("backend") or "core"), str(args["model"])))
    if name == "cortex_enhance_prompt":
        return _text(enhance_prompt(str(args["prompt"]), args.get("model")))
    if name == "cortex_image":
        backend = str(args.get("backend") or "core")
        if backend == "studio":
            return _text(_image_studio(args))
        return _text(_image_core(args))
    if name == "cortex_edit":
        url = resolve_ref(str(args["image"]))
        op = str(args.get("op") or "edit")
        wait = bool(args.get("wait", True))
        if op == "remove-bg":
            return _text(core_generate("image", {"model": "remove-bg", "imageUrls": [url], "prompt": "remove background"}, wait=wait))
        if op == "upscale":
            return _text(core_generate("image", {"model": "upscale", "imageUrls": [url], "prompt": "upscale"}, wait=wait))
        model = args.get("model") or "nano-banana-2"
        prompt = str(args.get("prompt") or "edit this image as instructed")
        return _text(core_generate("image", {"model": model, "prompt": prompt, "imageUrls": [url]}, wait=wait))
    if name == "cortex_video":
        payload: dict[str, Any] = {
            "prompt": str(args.get("prompt") or ""),
            "model": args.get("model") or "minimax-h3",
        }
        if args.get("duration") is not None:
            payload["duration"] = int(args["duration"])
        if args.get("resolution"):
            payload["resolution"] = args["resolution"]
        if args.get("ratio"):
            payload["ratio"] = args["ratio"]
        if args.get("generate_audio"):
            payload["generateAudio"] = True
        ri = resolve_refs(_str_list(args.get("reference_images")))
        rv = resolve_refs(_str_list(args.get("reference_videos")))
        ra = resolve_refs(_str_list(args.get("reference_audios")))
        if ri:
            payload["referenceImages"] = ri
        if rv:
            payload["referenceVideos"] = rv
        if ra:
            payload["referenceAudios"] = ra
        if args.get("first_frame"):
            payload["firstFrameImage"] = resolve_ref(str(args["first_frame"]))
        if args.get("last_frame"):
            payload["lastFrameImage"] = resolve_ref(str(args["last_frame"]))
        if payload["model"] == "wan-2-6" and not payload.get("referenceImages"):
            return _text({"error": "wan-2-6 requires reference_images (1 still)"})
        if payload["model"] == "video-upscale" and not payload.get("referenceVideos"):
            return _text({"error": "video-upscale requires reference_videos (1 mp4)"})
        return _text(core_generate("video", payload, wait=bool(args.get("wait", True)), timeout_s=1800))
    if name == "cortex_speech":
        payload = {
            "model": "speech-2-8-hd",
            "prompt": str(args["text"]),
            "voiceId": args.get("voice_id") or "Turkish_Energetic_Speaker_v3",
            "languageBoost": args.get("language") or "Turkish",
            "format": "mp3",
        }
        if args.get("emotion"):
            payload["emotion"] = args["emotion"]
        if args.get("speed") is not None:
            payload["speed"] = float(args["speed"])
        if args.get("subtitles") is not None:
            payload["subtitles"] = bool(args["subtitles"])
        return _text(core_generate("audio", payload, wait=bool(args.get("wait", True))))
    if name == "cortex_music":
        backend = str(args.get("backend") or "core")
        wait = bool(args.get("wait", True))
        if backend == "core":
            payload = {
                "model": "music-3",
                "prompt": str(args["prompt"]),
                "instrumental": bool(args.get("instrumental", True)),
            }
            if args.get("lyrics"):
                payload["lyrics"] = args["lyrics"]
                payload["instrumental"] = False
            return _text(core_generate("audio", payload, wait=wait))
        payload = {
            "prompt": str(args["prompt"]),
            "instrumental": bool(args.get("instrumental", True)),
        }
        if args.get("lyrics"):
            payload["lyrics"] = args["lyrics"]
            payload["instrumental"] = False
        return _text(studio_music(payload, wait=wait))
    if name == "cortex_lyrics":
        idea = str(args["idea"])
        out = lyrics_enhance(idea, args.get("style"), str(args.get("language") or "tr"))
        lyrics = None
        if isinstance(out.get("data"), dict):
            lyrics = out["data"].get("lyrics")
        if args.get("tokenize", True) and lyrics:
            out["tokenize"] = lyrics_tokenize(str(lyrics))
        return _text(out)
    if name == "cortex_sfx":
        return _text(
            studio_sfx(
                str(args["text"]),
                duration_seconds=float(args["duration_seconds"]) if args.get("duration_seconds") is not None else None,
                loop=bool(args.get("loop", False)),
            )
        )
    if name == "cortex_voices":
        return _text(voices(str(args.get("language") or "turkish"), int(args.get("limit") or 20)))
    if name == "cortex_voice_design":
        payload = {"model": "voice-design", "prompt": str(args["prompt"])}
        if args.get("preview_text"):
            payload["previewText"] = args["preview_text"]
        return _text(core_generate("audio", payload, wait=bool(args.get("wait", True))))
    if name == "cortex_voice_clone":
        url = resolve_ref(str(args["audio"]))
        payload: dict[str, Any] = {"model": "voice-clone", "referenceAudios": [url]}
        if args.get("preview_text"):
            payload["prompt"] = args["preview_text"]
        return _text(core_generate("audio", payload, wait=bool(args.get("wait", True))))
    if name == "cortex_upload":
        return _text(upload(str(args["path"])))
    if name == "cortex_job":
        jid = str(args["job_id"])
        if args.get("wait"):
            return _text(poll_core_job(jid))
        from client import CORE, http

        status, data, _ = http("GET", f"{CORE}/jobs/{jid}", timeout=30)
        return _text({"http": status, "data": data})
    if name == "cortex_chat":
        return _text(
            chat(
                str(args.get("gateway") or "api-v2"),
                str(args["model"]),
                str(args["prompt"]),
                max_tokens=int(args.get("max_tokens") or 1024),
            )
        )
    if name == "cortex_jury":
        return _text(
            jury(
                str(args["prompt"]),
                max_tokens=int(args.get("max_tokens") or 800),
                system=args.get("system"),
            )
        )
    if name == "cortex_embed":
        texts = args.get("texts") or []
        if isinstance(texts, str):
            texts = [texts]
        return _text(embed([str(t) for t in texts], str(args.get("model") or "text-embedding-3-small")))
    return {"content": [{"type": "text", "text": f"unknown tool: {name}"}], "isError": True}


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return _ok(
            mid,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "cortex", "version": "1.1.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _ok(mid, {})
    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            return _ok(mid, call_tool(str(name), args if isinstance(args, dict) else {}))
        except Exception as e:
            return _ok(
                mid,
                {"content": [{"type": "text", "text": f"tool error: {e}"}], "isError": True},
            )
    if mid is not None:
        return _err(mid, -32601, f"method not found: {method}")
    return None


def main() -> None:
    if not load_key():
        sys.stderr.write("cortex-mcp: CORTEX_API_KEY missing (cortex.env)\n")
        sys.stderr.flush()
    stdin = sys.stdin
    while True:
        line = stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
