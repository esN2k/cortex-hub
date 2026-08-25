#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    env_file = root / "cortex.env"
    if not env_file.is_file():
        print("missing cortex.env")
        return 1
    key = ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("CORTEX_API_KEY="):
            key = line.split("=", 1)[1].strip()
    if not key.startswith("sk-"):
        print("CORTEX_API_KEY missing in cortex.env")
        return 1
    os.environ["CORTEX_API_KEY"] = key
    oc = Path.home() / ".config" / "opencode"
    (oc / "plugins").mkdir(parents=True, exist_ok=True)
    (oc / "skills" / "cortex").mkdir(parents=True, exist_ok=True)
    cfg = json.loads((root / "config" / "opencode.json").read_text(encoding="utf-8"))
    run = root / "mcp" / "run.cmd"
    if os.name == "nt" and run.is_file():
        cfg["mcp"]["servers"]["cortex"]["command"] = ["cmd", "/c", str(run)]
        cfg["mcp"]["servers"]["cortex"].pop("cwd", None)
    else:
        cfg["mcp"]["servers"]["cortex"]["command"] = [sys.executable, str(root / "mcp" / "server.py")]
        cfg["mcp"]["servers"]["cortex"]["cwd"] = str(root)
    (oc / "opencode.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(root / "plugins" / "cortex.ts", oc / "plugins" / "cortex.ts")
    shutil.copy2(root / "plugins" / "cortex-fallback.ts", oc / "plugins" / "cortex-fallback.ts")
    shutil.copy2(root / "skills" / "cortex" / "SKILL.md", oc / "skills" / "cortex" / "SKILL.md")
    shutil.copy2(env_file, oc / "cortex.env")
    print("wrote", oc / "opencode.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
