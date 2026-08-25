#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
from client import fetch_url, lyrics_tokenize  # noqa: E402


def main() -> int:
    f = fetch_url("https://example.com", 8000)
    print("FETCH", f.get("http"), "chars", f.get("chars"))
    tok = lyrics_tokenize("merhaba dunya chorus")
    print("TOKENIZE", tok.get("http"), tok.get("data"))
    ok = f.get("http") == 200 and int(f.get("chars") or 0) > 20
    print("SMOKE_FETCH", "PASS" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
