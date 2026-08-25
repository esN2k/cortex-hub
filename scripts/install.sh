#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Cortex Hub install from $ROOT"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
if [[ ! -f "$ROOT/cortex.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/cortex.env"
  echo "Created cortex.env — edit CORTEX_API_KEY then re-run."
  exit 1
fi
# shellcheck disable=SC1091
set -a
source "$ROOT/cortex.env"
set +a
mkdir -p "$HOME/.config/opencode/plugins" "$HOME/.config/opencode/skills/cortex"
cp "$ROOT/config/opencode.json" "$HOME/.config/opencode/opencode.json"
cp "$ROOT/plugins/"*.ts "$HOME/.config/opencode/plugins/"
cp "$ROOT/skills/cortex/SKILL.md" "$HOME/.config/opencode/skills/cortex/"
cp "$ROOT/cortex.env" "$HOME/.config/opencode/cortex.env"
echo "OpenCode config written. Restart OpenCode."
echo "Hub: python3 $ROOT/hub/server.py"
echo "Smoke: python3 $ROOT/mcp/smoke.py"
