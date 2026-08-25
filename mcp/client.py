# -*- coding: utf-8 -*-
"""CortexAI HTTP client — tek anahtar, tum gateway'ler."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HOME = Path.home()
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_CANDIDATES = [
    Path(os.environ["CORTEX_ENV_FILE"]) if os.environ.get("CORTEX_ENV_FILE") else None,
    _REPO_ROOT / "cortex.env",
    HOME / ".config" / "opencode" / "cortex.env",
    Path(__file__).resolve().parent / "cortex.env",
]
ENV_FILE = next((p for p in _ENV_CANDIDATES if p is not None and p.is_file()), HOME / ".config" / "opencode" / "cortex.env")
OUT_DIR = Path(os.environ.get("CORTEX_OUT_DIR") or (_REPO_ROOT / "cortex-out" if (_REPO_ROOT / "mcp").is_dir() or (_REPO_ROOT / "hub").is_dir() else HOME / ".config" / "opencode" / "cortex-out"))

GATEWAYS = {
    "app": "https://app.claude.gg",
    "claude": "https://claude.gg",
    "api": "https://api.claude.gg",
    "llm": "https://llm.claude.gg",
    "llm-v2": "https://llm-v2.claude.gg",
    "api-v2": "https://api-v2.claude.gg",
    "grok": "https://grok-beta-v4.claude.gg",
    "studio": "https://studio.claude.gg",
    "core": "https://core.claude.gg",
}

CORE = GATEWAYS["core"] + "/v1"
STUDIO = GATEWAYS["studio"] + "/v1"
APIV2 = GATEWAYS["api-v2"] + "/v1"


def load_key() -> str:
    key = (os.environ.get("CORTEX_API_KEY") or "").strip()
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("CORTEX_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _headers(key: str | None = None, extra: dict[str, str] | None = None) -> dict[str, str]:
    k = key if key is not None else load_key()
    h = {
        "Accept": "application/json",
        "User-Agent": "opencode-cortex-mcp/1.0",
    }
    if k:
        h["Authorization"] = f"Bearer {k}"
        h["x-api-key"] = k
    if extra:
        h.update(extra)
    return h


def http(
    method: str,
    url: str,
    *,
    body: Any | None = None,
    key: str | None = None,
    timeout: int = 120,
    extra_headers: dict[str, str] | None = None,
    raw: bool = False,
) -> tuple[int, Any, dict[str, str]]:
    data = None
    headers = _headers(key, extra_headers)
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            data = bytes(body)
            headers.setdefault("Content-Type", "application/octet-stream")
        else:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            if raw:
                return resp.status, raw_bytes, hdrs
            text = raw_bytes.decode("utf-8", errors="replace")
            if not text.strip():
                return resp.status, None, hdrs
            try:
                return resp.status, json.loads(text), hdrs
            except json.JSONDecodeError:
                return resp.status, text, hdrs
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        parsed: Any = err_body
        try:
            parsed = json.loads(err_body) if err_body else {"error": str(e)}
        except json.JSONDecodeError:
            parsed = {"error": err_body or str(e), "status": e.code}
        hdrs = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return e.code, parsed, hdrs
    except Exception as e:
        return 0, {"error": str(e)}, {}


def dump(obj: Any, limit: int = 12000) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    if len(text) > limit:
        return text[:limit] + f"\n… truncated ({len(text)} chars)"
    return text


def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    status, data, _ = http(
        "POST",
        f"{APIV2}/web/search",
        body={"query": query, "num_results": max(1, min(int(num_results), 10))},
        timeout=60,
    )
    return {"http": status, "data": data}


def chat(
    gateway: str,
    model: str,
    prompt: str,
    *,
    max_tokens: int = 2048,
    system: str | None = None,
) -> dict[str, Any]:
    base = GATEWAYS.get(gateway)
    if not base:
        return {"error": f"unknown gateway: {gateway}", "known": list(GATEWAYS)}
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    status, data, _ = http(
        "POST",
        f"{base}/v1/chat/completions",
        body={"model": model, "messages": messages, "max_tokens": max_tokens},
        timeout=180,
    )
    text = None
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices:
            msg = (choices[0] or {}).get("message") or {}
            text = msg.get("content")
        if text is None and isinstance(data.get("text"), str):
            text = data["text"]
        content = data.get("content")
        if text is None and isinstance(content, list) and content:
            text = content[0].get("text") if isinstance(content[0], dict) else None
    return {"http": status, "text": text, "raw": data}


def core_generate(kind: str, payload: dict[str, Any], *, wait: bool = True, timeout_s: int = 900) -> dict[str, Any]:
    kind = kind.strip().lower()
    if kind == "music":
        kind = "audio"
    if kind not in {"image", "video", "audio"}:
        return {"error": "kind must be image|video|audio|music"}
    status, data, hdrs = http("POST", f"{CORE}/generate/{kind}", body=payload, timeout=60)
    quota = {k: hdrs.get(k) for k in hdrs if k.startswith("x-quota")}
    if status not in (200, 202) or not isinstance(data, dict):
        return {"http": status, "error": data, "quota": quota}
    job_id = data.get("id") or data.get("job_id")
    result: dict[str, Any] = {"http": status, "job": data, "quota": quota}
    if wait and job_id:
        result["polled"] = poll_core_job(str(job_id), timeout_s=timeout_s)
        job = result["polled"]
        if isinstance(job, dict) and job.get("status") == "success":
            saved = save_core_media(str(job_id), kind)
            result["saved"] = saved
            result["public_url"] = _abs_core(job.get("public_url"))
            result["output_url"] = _abs_core(job.get("output_url"))
    return result


def poll_core_job(job_id: str, *, timeout_s: int = 900, interval: float = 6.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last: Any = None
    while time.time() < deadline:
        status, data, _ = http("GET", f"{CORE}/jobs/{job_id}", timeout=30)
        last = data
        if isinstance(data, dict):
            st = data.get("status")
            if st in {"success", "failed"}:
                return data
        time.sleep(interval)
    return {"error": "poll_timeout", "last": last, "job_id": job_id}


def _abs_core(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith("http"):
        return path
    return GATEWAYS["core"] + path


def save_core_media(job_id: str, kind: str) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = {"image": "jpg", "video": "mp4", "audio": "mp3"}.get(kind, "bin")
    dest = OUT_DIR / f"{job_id}.{ext}"
    status, data, hdrs = http("GET", f"{CORE}/media/{job_id}", timeout=180, raw=True)
    if status != 200 or not isinstance(data, (bytes, bytearray)):
        return {"http": status, "error": "download_failed", "body": data if not isinstance(data, bytes) else None}
    dest.write_bytes(data)
    ctype = hdrs.get("content-type", "")
    return {"path": str(dest), "bytes": dest.stat().st_size, "content_type": ctype}


def studio_image(payload: dict[str, Any], *, wait: bool = True) -> dict[str, Any]:
    body = dict(payload)
    body.setdefault("wait", wait)
    if wait:
        body.setdefault("poll_timeout_ms", 180000)
    status, data, _ = http("POST", f"{STUDIO}/images/generations", body=body, timeout=200)
    saved: list[str] = []
    if isinstance(data, dict):
        items = data.get("data") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("content_url") or item.get("preview_url")
            if url and item.get("status") in (None, "completed"):
                p = save_studio_url(str(url), str(item.get("id") or data.get("id") or "img"))
                if p:
                    saved.append(p)
                    item["saved"] = p
    return {"http": status, "data": data, "saved": saved}


def save_studio_url(url: str, name: str) -> str | None:
    if url.startswith("/"):
        url = GATEWAYS["studio"] + url
    status, data, _ = http("GET", url, timeout=120, raw=True)
    if status != 200 or not isinstance(data, (bytes, bytearray)):
        return None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:80]
    ext = "png"
    dest = OUT_DIR / f"{safe}.{ext}"
    dest.write_bytes(data)
    return str(dest)


def studio_music(payload: dict[str, Any], *, wait: bool = True, timeout_s: int = 300) -> dict[str, Any]:
    status, data, _ = http("POST", f"{STUDIO}/music/generations", body=payload, timeout=60)
    if not wait or not isinstance(data, dict):
        return {"http": status, "data": data}
    job_id = data.get("id")
    if not job_id:
        return {"http": status, "data": data}
    deadline = time.time() + timeout_s
    last = data
    while time.time() < deadline:
        st, polled, _ = http("GET", f"{STUDIO}/music/generations/{job_id}", timeout=30)
        last = polled
        if isinstance(polled, dict):
            state = polled.get("status")
            variants = polled.get("variants") or []
            done = state in {"completed", "failed"}
            if variants and all(isinstance(v, dict) and v.get("status") in {"completed", "failed"} for v in variants):
                done = True
            if done:
                saved = []
                for v in variants if variants else [polled]:
                    if not isinstance(v, dict):
                        continue
                    audio = v.get("audio_url")
                    if audio and v.get("status") == "completed":
                        p = save_studio_url(str(audio), str(v.get("id") or "music"))
                        if p:
                            saved.append(p)
                            v["saved"] = p
                return {"http": st, "data": polled, "saved": saved}
        time.sleep(2)
    return {"http": status, "data": last, "error": "poll_timeout"}


def upload(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"error": f"file not found: {path}"}
    raw = p.read_bytes()
    if len(raw) > 50 * 1024 * 1024:
        return {"error": "file > 50MB"}
    extra = {}
    suffix = p.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }.get(suffix, "application/octet-stream")
    extra["Content-Type"] = mime
    status, data, _ = http("POST", f"{CORE}/uploads", body=raw, extra_headers=extra, timeout=120)
    return {"http": status, "data": data}


def quota() -> dict[str, Any]:
    key = load_key()
    if not key:
        return {"error": "CORTEX_API_KEY missing"}
    q = urllib.parse.quote(key)
    out: dict[str, Any] = {}
    checks = [
        ("claude.gg", f"https://claude.gg/api/me?key={q}"),
        ("app.claude.gg", f"https://app.claude.gg/api/me?key={q}"),
        ("api.claude.gg", f"https://api.claude.gg/api/me?key={q}"),
        ("llm.claude.gg", f"https://llm.claude.gg/api/me?key={q}"),
        ("studio.usage", f"{STUDIO}/usage"),
        ("core.me", f"{CORE}/me"),
        ("core.usage", f"{CORE}/usage"),
    ]
    for name, url in checks:
        status, data, _ = http("GET", url, timeout=20)
        out[name] = {"http": status, "data": data}
    return out


def catalog(which: str = "all") -> dict[str, Any]:
    which = (which or "all").lower()
    out: dict[str, Any] = {}
    mapping = {
        "app": "https://app.claude.gg/v1/models",
        "claude": "https://claude.gg/v1/models",
        "api": "https://api.claude.gg/v1/models",
        "llm": "https://llm.claude.gg/v1/models",
        "llm-v2": "https://llm-v2.claude.gg/v1/models",
        "api-v2": "https://api-v2.claude.gg/v1/models",
        "grok": "https://grok-beta-v4.claude.gg/v1/models",
        "studio": f"{STUDIO}/models",
        "core": f"{CORE}/models",
    }
    targets = mapping if which == "all" else {which: mapping.get(which, "")}
    for name, url in targets.items():
        if not url:
            out[name] = {"error": "unknown catalog"}
            continue
        status, data, _ = http("GET", url, timeout=30)
        ids: list[str] = []
        if isinstance(data, dict):
            rows = data.get("data") or data.get("models") or []
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        ids.append(str(row.get("id") or row.get("name") or ""))
                    elif isinstance(row, str):
                        ids.append(row)
        out[name] = {"http": status, "ids": [i for i in ids if i], "count": len(ids)}
    return out


def voices(language: str = "turkish", limit: int = 20) -> dict[str, Any]:
    q = urllib.parse.urlencode({"language": language, "limit": str(limit)})
    status, data, _ = http("GET", f"{CORE}/voices?{q}", timeout=30)
    return {"http": status, "data": data}
