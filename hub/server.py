# -*- coding: utf-8 -*-
"""Cortex Hub — yerel kurulum + probe + hata raporu paneli. 127.0.0.1:3848"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _cand in (ROOT / "mcp", ROOT / "cortex-mcp", HERE / "mcp"):
    if (_cand / "client.py").is_file():
        sys.path.insert(0, str(_cand))
        break
from client import (  # noqa: E402
    OUT_DIR,
    catalog,
    chat,
    core_generate,
    dump,
    load_key,
    quota,
)

HOST = "127.0.0.1"
PORT = 3848
DATA = HERE / "data"
HISTORY = DATA / "probes.jsonl"
CATALOG_PATH = HERE / "catalog.json"


def _now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def read_history(limit: int = 200) -> list[dict[str, Any]]:
    if not HISTORY.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in HISTORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()
    return rows[:limit]


def append_history(row: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def redact(text: str) -> str:
    import re

    key = load_key()
    if key and key in text:
        text = text.replace(key, key[:7] + "…" + key[-4:])
    return re.sub(r"sk-[a-zA-Z0-9]{8,}", lambda m: m.group(0)[:7] + "…" + m.group(0)[-4:], text)


def probe_one(gateway: str, model: str, name: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = chat(gateway, model, "Reply with exactly: PONG", max_tokens=32)
    except Exception as e:
        result = {"http": 0, "text": None, "raw": {"error": str(e), "trace": traceback.format_exc()[-800:]}}
    ms = int((time.perf_counter() - t0) * 1000)
    http = int(result.get("http") or 0)
    text = result.get("text")
    raw = result.get("raw")
    err = None
    if isinstance(raw, dict):
        err = raw.get("error") or raw.get("message")
    ok = http == 200 and bool(text)
    row = {
        "id": f"{int(time.time() * 1000)}-{gateway}-{model}".replace("/", "_")[:80],
        "time": _now(),
        "iso": _iso(),
        "gateway": gateway,
        "model": model,
        "name": name,
        "http": http,
        "ms": ms,
        "ok": ok,
        "status": "completed" if ok else "error",
        "text": (str(text)[:80] if text else None),
        "error": redact(json.dumps(err, ensure_ascii=False)[:800]) if err else None,
    }
    append_history(row)
    return row


def probe_all() -> list[dict[str, Any]]:
    cat = load_catalog()
    out = []
    for item in cat.get("probes") or []:
        out.append(probe_one(item["gateway"], item["model"], item["name"]))
        time.sleep(0.4)
    return out


def setup_snippets() -> dict[str, Any]:
    key_hint = "CORTEX_API_KEY (cortex.env)"
    return {
        "opencode": {
            "title": "OpenCode",
            "steps": [
                "Anahtar: ~/.config/opencode/cortex.env → CORTEX_API_KEY=sk-…",
                "Config zaten: model grok/grok-4.6-max, yedek Sonnet thinking, MCP cortex.",
                "OpenCode’u kapat/aç. Yeni oturum Grok Max ile açılır.",
            ],
            "snippet": '{\n  "model": "grok/grok-4.6-max",\n  "providers.grok.settings.baseURL": "https://grok-beta-v4.claude.gg"\n}',
        },
        "claude-code": {
            "title": "Claude Code CLI",
            "steps": [
                "~/.claude/settings.json → env bloğu",
                "ANTHROPIC_BASE_URL=https://app.claude.gg",
                "ANTHROPIC_AUTH_TOKEN=<aynı sk>",
                "model: claude-sonnet-4-6-thinking",
            ],
            "snippet": json.dumps(
                {
                    "env": {
                        "ANTHROPIC_BASE_URL": "https://app.claude.gg",
                        "ANTHROPIC_AUTH_TOKEN": key_hint,
                    },
                    "model": "claude-sonnet-4-6-thinking",
                },
                indent=2,
            ),
        },
        "cowork": {
            "title": "Claude Desktop / Cowork",
            "steps": [
                "Help → Troubleshooting → Enable Developer Mode (yeniden başlar)",
                "Developer → Configure Third-Party Inference",
                "Gateway: https://app.claude.gg  ·  bearer  ·  model: claude-sonnet-4-6",
                "thinking için ayrıca claude-sonnet-4-6-thinking ekle",
                "Apply locally",
            ],
            "snippet": "Gateway base URL: https://app.claude.gg\nModel ID: claude-sonnet-4-6-thinking",
        },
        "cline": {
            "title": "Cline",
            "steps": [
                "Provider: Anthropic (Sonnet) veya OpenAI Compatible (Grok/GPT)",
                "Use Custom Base URL",
                "Sonnet: https://app.claude.gg  model claude-sonnet-4-6-thinking",
                "Grok: https://grok-beta-v4.claude.gg  model grok-4.6-max",
            ],
            "snippet": json.dumps(
                {
                    "provider": "anthropic",
                    "baseUrl": "https://app.claude.gg",
                    "model": "claude-sonnet-4-6-thinking",
                    "apiKey": key_hint,
                },
                indent=2,
            ),
        },
        "roo": {
            "title": "Roo / Zoo Code",
            "steps": [
                "OpenAI Compatible",
                "Base URL: https://grok-beta-v4.claude.gg/v1  (veya app.claude.gg/v1)",
                "Model: grok-4.6-max veya claude-sonnet-4-6-thinking",
            ],
            "snippet": "baseURL=https://grok-beta-v4.claude.gg/v1\nmodel=grok-4.6-max",
        },
        "cursor-byok": {
            "title": "cursor-byok / Cursor Assistant",
            "steps": [
                "Model Settings → OpenAI protocol",
                "Endpoint + model ID + aynı API key",
                "Aşağıdaki preset’i içe aktar (anahtar yok — sen yapıştırırsın)",
            ],
            "snippet": json.dumps(
                {
                    "models": [
                        {
                            "name": "Grok 4.6 Max",
                            "protocol": "openai",
                            "baseURL": "https://grok-beta-v4.claude.gg",
                            "modelID": "grok-4.6-max",
                            "context": 450000,
                            "maxOutput": 32768,
                            "reasoningEffort": "xhigh",
                        },
                        {
                            "name": "Sonnet 4.6 Thinking",
                            "protocol": "openai",
                            "baseURL": "https://app.claude.gg",
                            "modelID": "claude-sonnet-4-6-thinking",
                            "context": 200000,
                            "maxOutput": 64000,
                            "reasoningEffort": "max",
                        },
                    ]
                },
                indent=2,
            ),
        },
        "trae": {
            "title": "TRAE",
            "steps": [
                "Settings → Models → Custom Config",
                "API Format: Anthropic Messages",
                "Full URL ON: https://app.claude.gg",
                "Model: claude-sonnet-4-6-thinking",
            ],
            "snippet": "https://app.claude.gg  ·  claude-sonnet-4-6-thinking",
        },
    }


def make_report(row: dict[str, Any] | None, extra: str = "") -> str:
    q = {}
    try:
        q = quota()
    except Exception:
        q = {"error": "quota fetch failed"}
    key = load_key()
    lines = [
        "## Cortex bug report",
        f"- Time: {_now()} (local)",
        f"- Key: {(key[:7] + '…' + key[-4:]) if key else 'MISSING'}",
        "- Client: (hangi uygulama — doldur)",
        f"- Gateway: {row.get('gateway') if row else '—'}",
        f"- Model: {row.get('model') if row else '—'}",
        f"- Display: {row.get('name') if row else '—'}",
        f"- HTTP: {row.get('http') if row else '—'}",
        f"- Latency: {row.get('ms') if row else '—'} ms",
        f"- Status: {row.get('status') if row else '—'}",
        f"- Reply preview: {row.get('text') if row else '—'}",
        f"- Error: {row.get('error') if row else '—'}",
        "",
        "### Quota snapshot",
        "```json",
        redact(dump(q, limit=4000)),
        "```",
        "",
        "### Notes",
        extra.strip() or "(ne yaptın, beklenen vs.)",
        "",
        "Anahtar, prompt ve kişisel dosya yolu yok. Forum / Discord’a yapıştırılabilir.",
    ]
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[hub] " + (fmt % args) + "\n")

    def _json(self, obj: Any, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self) -> None:
        path = HERE / "index.html"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            obj = json.loads(raw.decode("utf-8"))
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._html()
            return
        if path == "/api/health":
            self._json({"ok": True, "key": bool(load_key()), "time": _now()})
            return
        if path == "/api/quota":
            self._json(quota())
            return
        if path == "/api/catalog":
            live = {}
            try:
                live = catalog("all")
            except Exception as e:
                live = {"error": str(e)}
            self._json({"static": load_catalog(), "live": live, "key": bool(load_key())})
            return
        if path == "/api/history":
            self._json({"rows": read_history()})
            return
        if path == "/api/setup":
            self._json(setup_snippets())
            return
        if path == "/api/media":
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            items = []
            for p in sorted(OUT_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:40]:
                if p.is_file():
                    items.append({"name": p.name, "bytes": p.stat().st_size, "url": "/media/" + p.name})
            self._json({"dir": str(OUT_DIR), "items": items})
            return
        if path.startswith("/media/"):
            name = Path(path).name
            dest = (OUT_DIR / name).resolve()
            if dest.parent != OUT_DIR.resolve() or not dest.is_file():
                self.send_error(404)
                return
            data = dest.read_bytes()
            ctype = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".mp3": "audio/mpeg",
                ".mp4": "video/mp4",
                ".wav": "audio/wav",
            }.get(dest.suffix.lower(), "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_json()
        if path == "/api/probe":
            if body.get("all"):
                self._json({"rows": probe_all()})
                return
            gw = str(body.get("gateway") or "")
            model = str(body.get("model") or "")
            name = str(body.get("name") or model)
            if not gw or not model:
                self._json({"error": "gateway and model required"}, 400)
                return
            self._json(probe_one(gw, model, name))
            return
        if path == "/api/report":
            rid = str(body.get("id") or "")
            row = next((r for r in read_history(500) if r.get("id") == rid), None)
            if not row and body.get("gateway"):
                row = {
                    "gateway": body.get("gateway"),
                    "model": body.get("model"),
                    "name": body.get("name"),
                    "http": body.get("http"),
                    "ms": body.get("ms"),
                    "status": body.get("status"),
                    "text": body.get("text"),
                    "error": body.get("error"),
                }
            self._json({"markdown": make_report(row, str(body.get("notes") or ""))})
            return
        if path == "/api/studio":
            kind = str(body.get("kind") or "")
            prompt = str(body.get("prompt") or body.get("text") or "")
            wait = bool(body.get("wait", True))
            if not prompt:
                self._json({"error": "prompt required"}, 400)
                return
            if kind == "image":
                payload = {"prompt": prompt, "model": body.get("model") or "seedream-5"}
                if body.get("aspect_ratio"):
                    payload["aspectRatio"] = body["aspect_ratio"]
                self._json(core_generate("image", payload, wait=wait))
                return
            if kind == "video":
                payload = {
                    "prompt": prompt,
                    "model": body.get("model") or "minimax-h3",
                    "duration": int(body.get("duration") or 5),
                    "resolution": body.get("resolution") or "768P",
                }
                self._json(core_generate("video", payload, wait=wait, timeout_s=1800))
                return
            if kind == "speech":
                payload = {
                    "model": "speech-2-8-hd",
                    "prompt": prompt,
                    "voiceId": body.get("voice_id") or "Turkish_Energetic_Speaker_v3",
                    "languageBoost": body.get("language") or "Turkish",
                    "format": "mp3",
                }
                self._json(core_generate("audio", payload, wait=wait))
                return
            if kind == "music":
                payload = {
                    "model": "music-3",
                    "prompt": prompt,
                    "instrumental": bool(body.get("instrumental", True)),
                }
                if body.get("lyrics"):
                    payload["lyrics"] = body["lyrics"]
                    payload["instrumental"] = False
                self._json(core_generate("audio", payload, wait=wait))
                return
            self._json({"error": "kind must be image|video|speech|music"}, 400)
            return
        self.send_error(404)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"Cortex Hub  {url}   (Ctrl+C durdur)")
    if os.environ.get("CORTEX_HUB_NO_BROWSER") != "1":
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstop")


if __name__ == "__main__":
    main()
