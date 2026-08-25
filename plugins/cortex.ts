import { Plugin } from "@opencode-ai/plugin"

export default Plugin.define({
  id: "cortex",
  async setup(ctx) {
    await ctx.websearch.transform((draft) => {
      draft.add({
        id: "cortex",
        name: "Cortex api-v2 (5000/day)",
        execute: async ({ query }, { signal }) => {
          let key = process.env.CORTEX_API_KEY
          if (!key) {
            const envPath = `${process.env.USERPROFILE}\\.config\\opencode\\cortex.env`
            try {
              const text = await Bun.file(envPath).text()
              const line = text.split(/\r?\n/).find((row) => row.startsWith("CORTEX_API_KEY="))
              key = line ? line.slice("CORTEX_API_KEY=".length).trim() : undefined
            } catch {
              key = undefined
            }
          }
          if (!key) {
            throw new Error("CORTEX_API_KEY missing (~/.config/opencode/cortex.env)")
          }
          const response = await fetch("https://api-v2.claude.gg/v1/web/search", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${key}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ query, num_results: 5 }),
            signal,
          })
          const data = (await response.json()) as {
            results?: Array<{ url?: string; title?: string; content?: string; snippet?: string }>
            data?: Array<{ url?: string; title?: string; content?: string; snippet?: string }>
            error?: unknown
          }
          if (!response.ok) {
            throw new Error(`cortex search HTTP ${response.status}: ${JSON.stringify(data)}`)
          }
          const rows = data.results || data.data || []
          return rows.map((row) => ({
            url: String(row.url || ""),
            title: String(row.title || row.url || "result"),
            content: String(row.content || row.snippet || ""),
            time: {},
          }))
        },
      })
      draft.default.set("cortex")
    })
  },
})
