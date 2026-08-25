# Agent notes

- Default coding model for subscribers: `grok/grok-4.6-max`
- Fallback: `app-cortex/claude-sonnet-4-6-thinking`
- Media, search, jury, and embeddings are **MCP tools**, not the session model
- Stills: enhance_prompt → image (with image_urls). Video: wan-2-6 + still or H3 + first_frame
- Jury uses grok/app/api-v2 buckets; embeddings use api.claude.gg
- Do not generate exam questions for KPSS workflows
- Do not commit `cortex.env`
- Probe 402/503: produce a Hub bug report instead of retry storms
- Quality over speed; cost is ignored by design
