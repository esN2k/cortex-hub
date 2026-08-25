#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ping every catalog probe model. No Hub required. Exit 2 if any fail (expected on 402/503)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
from client import chat  # noqa: E402

CAT = json.loads((ROOT / "hub" / "catalog.json").read_text(encoding="utf-8"))


def main() -> int:
    rows = []
    for item in CAT.get("probes") or []:
        t0 = time.perf_counter()
        r = chat(item["gateway"], item["model"], "Reply with exactly: PONG", max_tokens=32)
        ms = int((time.perf_counter() - t0) * 1000)
        http = int(r.get("http") or 0)
        text = r.get("text")
        raw = r.get("raw")
        err = None
        if isinstance(raw, dict):
            err = raw.get("error") or raw.get("message")
        ok = http == 200 and bool(text)
        row = {
            "gateway": item["gateway"],
            "model": item["model"],
            "name": item["name"],
            "http": http,
            "ms": ms,
            "ok": ok,
            "text": (str(text)[:80] if text else None),
            "error": json.dumps(err, ensure_ascii=False)[:400] if err else None,
        }
        rows.append(row)
        print(f"{'OK' if ok else 'FAIL':4} http={http} {ms:5}ms  {item['name']}")
        time.sleep(0.3)
    okn = sum(1 for x in rows if x["ok"])
    print(f"SUMMARY {okn}/{len(rows)}")
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0 if okn else 2


if __name__ == "__main__":
    raise SystemExit(main())
