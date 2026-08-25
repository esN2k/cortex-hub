# Agent notes

- Default coding model for subscribers: `grok/grok-4.6-max`
- Fallback: `app-cortex/claude-sonnet-4-6-thinking`
- Media and search are **tools**, not the session model
- Do not generate exam questions for KPSS workflows
- Do not commit `cortex.env`
- Probe 402/503: produce a Hub bug report instead of retry storms
- Quality over speed; cost is ignored by design
