import { Plugin } from "@opencode-ai/plugin"

const FALLBACK = {
  providerID: "app-cortex",
  id: "claude-sonnet-4-6-thinking",
} as const

function grokFailed(status: number): boolean {
  return status === 401 || status === 403 || status === 408 || status === 429 || status >= 500
}

export default Plugin.define({
  id: "cortex.fallback",
  async setup(ctx) {
    await ctx.catalog.transform((catalog) => {
      catalog.model.default.set("grok", "grok-4.6-max")
    })

    const switched = new Set<string>()

    await ctx.session.hook(
      "http.response",
      async (event) => {
        const status = event.response.status
        const sessionID = (event as { sessionID?: string }).sessionID
        if (!grokFailed(status) || !sessionID || switched.has(sessionID)) return
        switched.add(sessionID)
        try {
          await ctx.session.switchModel({ sessionID, model: FALLBACK })
          await ctx.session.synthetic({
            sessionID,
            text:
              `Grok 4.6 Max HTTP ${status} — yedek modele geçildi: ` +
              `app-cortex/claude-sonnet-4-6-thinking (kalite; maliyet/hız yok).`,
          })
        } catch (err) {
          console.error("cortex.fallback: switch failed", err)
        }
      },
      { providerID: "grok" },
    )
  },
})
