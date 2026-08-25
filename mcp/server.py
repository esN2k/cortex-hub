# -*- coding: utf-8 -*-
"""CortexAI MCP (stdio JSON-RPC 2.0) — studio / core / web search / quota / chat."""
from __future__ import annotations

import json
import sys
from typing import Any

from client import (
    catalog,
    chat,
    core_generate,
    dump,
    load_key,
    poll_core_job,
    quota,
    studio_image,
    studio_music,
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
        "name": "cortex_quota",
        "description": "Remaining daily quota across claude.gg / app / api / llm / studio / core.",
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
        "name": "cortex_image",
        "description": (
            "Generate an image. backend=core (GateAI, poll+save, default seedream-5) "
            "or studio (OpenAI-style, default gpt-image-2). Files land in ~/.config/opencode/cortex-out/"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "backend": {"type": "string", "enum": ["core", "studio"], "default": "core"},
                "model": {"type": "string"},
                "aspect_ratio": {"type": "string", "description": "16:9, 1:1, 9:16, ..."},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_video",
        "description": (
            "Generate video via core.claude.gg (default minimax-h3). "
            "duration 4-15s. Polls until done; saves mp4 under cortex-out. Can take minutes."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "model": {"type": "string", "default": "minimax-h3"},
                "duration": {"type": "integer", "minimum": 4, "maximum": 15, "default": 5},
                "resolution": {"type": "string", "enum": ["768P", "2K"], "default": "768P"},
                "ratio": {"type": "string"},
                "generate_audio": {"type": "boolean", "default": False},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_speech",
        "description": "TTS via core.claude.gg speech-2-8-hd. Default Turkish energetic voice.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "voice_id": {"type": "string", "default": "Turkish_Energetic_Speaker_v3"},
                "language": {"type": "string", "default": "Turkish"},
                "emotion": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cortex_music",
        "description": "Generate music. backend=studio (v1, two variants) or core (music-3).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "style / mood"},
                "backend": {"type": "string", "enum": ["studio", "core"], "default": "studio"},
                "instrumental": {"type": "boolean", "default": True},
                "lyrics": {"type": "string"},
                "wait": {"type": "boolean", "default": True},
            },
            "required": ["prompt"],
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
]


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "cortex_web_search":
        return _text(web_search(str(args["query"]), int(args.get("num_results") or 5)))
    if name == "cortex_quota":
        return _text(quota())
    if name == "cortex_catalog":
        return _text(catalog(str(args.get("which") or "all")))
    if name == "cortex_image":
        backend = str(args.get("backend") or "core")
        prompt = str(args["prompt"])
        wait = bool(args.get("wait", True))
        if backend == "studio":
            payload: dict[str, Any] = {
                "prompt": prompt,
                "model": args.get("model") or "gpt-image-2",
            }
            if args.get("aspect_ratio"):
                payload["aspect_ratio"] = args["aspect_ratio"]
            return _text(studio_image(payload, wait=wait))
        payload = {
            "prompt": prompt,
            "model": args.get("model") or "seedream-5",
        }
        if args.get("aspect_ratio"):
            payload["aspectRatio"] = args["aspect_ratio"]
        return _text(core_generate("image", payload, wait=wait))
    if name == "cortex_video":
        payload = {
            "prompt": str(args["prompt"]),
            "model": args.get("model") or "minimax-h3",
            "duration": int(args.get("duration") or 5),
            "resolution": args.get("resolution") or "768P",
        }
        if args.get("ratio"):
            payload["ratio"] = args["ratio"]
        if args.get("generate_audio"):
            payload["generateAudio"] = True
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
        return _text(core_generate("audio", payload, wait=bool(args.get("wait", True))))
    if name == "cortex_music":
        backend = str(args.get("backend") or "studio")
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
    if name == "cortex_voices":
        return _text(voices(str(args.get("language") or "turkish"), int(args.get("limit") or 20)))
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
                "serverInfo": {"name": "cortex", "version": "1.0.0"},
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
        sys.stderr.write("cortex-mcp: CORTEX_API_KEY missing (~/.config/opencode/cortex.env)\n")
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
