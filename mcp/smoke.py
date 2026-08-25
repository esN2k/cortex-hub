# -*- coding: utf-8 -*-
"""Duman testi: anahtar + katalog + web search. Uretim (gorsel/video) yok."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import catalog, load_key, web_search  # noqa: E402


def main() -> int:
    key = load_key()
    if not key:
        print("FAIL: CORTEX_API_KEY missing")
        return 1
    print(f"KEY: {key[:6]}…{key[-4:]} ({len(key)} chars)")
    cat = catalog("app")
    app = cat.get("app") or {}
    print("APP_MODELS", app.get("http"), app.get("ids"))
    cat2 = catalog("api-v2")
    v2 = cat2.get("api-v2") or {}
    print("APIV2_COUNT", v2.get("http"), v2.get("count"), (v2.get("ids") or [])[:8])
    cat3 = catalog("core")
    core = cat3.get("core") or {}
    print("CORE_COUNT", core.get("http"), core.get("count"))
    sr = web_search("Laguna S 2.1", 2)
    print("SEARCH_HTTP", sr.get("http"))
    data = sr.get("data")
    preview = json.dumps(data, ensure_ascii=False)[:500] if data is not None else "null"
    print("SEARCH_PREVIEW", preview)
    ok = bool(key) and app.get("http") == 200 and sr.get("http") in (200, 201)
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
