# Gateway map

All hosts share one `CORTEX_API_KEY` from [cortexai.io](https://cortexai.io).
Reset: **03:00 Europe/Istanbul**.

| id | Base URL | Protocol | Daily | Use as |
|----|----------|----------|-------|--------|
| grok | https://grok-beta-v4.claude.gg | OpenAI chat | beta pool | **Primary agent** `grok-4.6-max` |
| app | https://app.claude.gg | OpenAI + Anthropic | 2500 / 1000 per hour | **Fallback agent** `claude-sonnet-4-6-thinking` |
| claude | https://claude.gg | OpenAI | 2500 | Plain Sonnet (prefer app for IDEs) |
| api | https://api.claude.gg | OpenAI | 4000 | GPT-5, Grok-4, DeepSeek, Gemini |
| llm | https://llm.claude.gg | OpenAI | 2500 | Kimi, Qwen, GLM, DeepSeek V4 |
| llm-v2 | https://llm-v2.claude.gg | OpenAI | 2500 | Kimi K3 v2 aliases |
| api-v2 | https://api-v2.claude.gg | OpenAI + Anthropic + **POST /v1/web/search** | 5000 search | Ox Alpha, Laguna, Muse Spark |
| studio | https://studio.claude.gg | images + music | 500 media | Not an IDE model |
| core | https://core.claude.gg | async jobs | 1000 media + 2500 text | Video, image, TTS, music |

## Auth

```
Authorization: Bearer sk-...
# core also accepts x-api-key
```

## Health checks (no key)

- `GET {base}/v1/models`
- studio: https://studio.claude.gg/v1/status
- core: https://core.claude.gg/v1/models

## Quota (key)

- `GET https://app.claude.gg/api/me?key=`
- `GET https://studio.claude.gg/v1/usage`
- `GET https://core.claude.gg/v1/me`

Hub Overview calls these together.

## Official docs

- https://cortexai.com.tr/
- https://studio.claude.gg/docs.txt
- https://core.claude.gg/docs
