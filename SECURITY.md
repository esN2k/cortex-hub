# Security

## Secrets

- Store the key in `cortex.env` (gitignored) or the user environment.
- Never paste `sk-` into issues, PRs, Discord screenshots, or `docs/`.
- Hub bug reports mask the key (`sk-xxxxx…yyyy`).

## If a key leaked

1. Revoke/rotate at https://cortexai.io  
2. Update `cortex.env` and user env `CORTEX_API_KEY`  
3. Restart OpenCode / Claude Code / Hub

## Threat model

Hub binds **127.0.0.1:3848** only. Do not expose it to the LAN without auth.
MCP is stdio — it inherits the process environment.

## Contact

Open a private GitHub security advisory on this repo, or rotate first and then file an issue without the key.
