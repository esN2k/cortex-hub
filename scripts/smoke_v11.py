#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.1 extras: status, schema, enhance (helper), embed. No image/video."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
from client import embed, enhance_prompt, gateway_status, load_key, model_schema  # noqa: E402


def main() -> int:
    if not load_key():
        print("FAIL: no key")
        return 1
    st = gateway_status()
    print("STATUS studio", (st.get("studio") or {}).get("http"), "core", (st.get("core") or {}).get("http"))
    sch = model_schema("core", "seedream-5")
    print("SCHEMA", sch.get("http"), type(sch.get("data")).__name__)
    en = enhance_prompt("a red apple on wood, product photo")
    print("ENHANCE", en.get("http"))
    data = en.get("data") if isinstance(en.get("data"), dict) else {}
    if data.get("prompt"):
        print("ENHANCED_CHARS", len(str(data.get("prompt"))))
    em = embed(["Cortex Hub semantic test"])
    print("EMBED", em.get("http"), "dims", em.get("dims"), "count", em.get("count"))
    if em.get("http") != 200:
        print("EMBED_WARN api.claude.gg embeddings not live (tool still registered)")
    ok = (
        (st.get("studio") or {}).get("http") == 200
        and sch.get("http") == 200
        and en.get("http") in (200, 201)
    )
    print("SMOKE_V11", "PASS" if ok else "FAIL")
    if not ok:
        print(json.dumps({"status": st, "schema_http": sch.get("http"), "enhance": en, "embed": em}, ensure_ascii=False)[:1500])
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
