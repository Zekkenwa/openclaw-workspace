# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Custom Rules

### Web Search Tool
- **CRITICAL RULE:** Do NOT use the `country` parameter when calling the web search tool (e.g. `country: "ID"`). The default provider currently configured (Gemini) does not support country filtering and will throw an `unsupported_country` error. Leave the country filter blank/omitted.
- **Also omit `language`, `search_lang`, and `ui_lang`** with the Gemini provider. It returns `unsupported_language` when language filtering is supplied. Start with only `query` and `count` (plus non-filter fields only if necessary).
- If web search errors, times out, or an in-flight parallel search is aborted: **do not answer as though the search succeeded.** Retry once using a shorter, narrower query (still without unsupported filters). If it fails again, use `web_fetch` on authoritative/primary URLs or plainly state that live-search verification is unavailable; distinguish estimates from sourced facts. For exact Steam game facts (storage, player modes, current review state), prefer `web_fetch` of the official Steam store page or `https://store.steampowered.com/api/appdetails?appids=<APP_ID>`; verify the returned app name/app ID before trusting it, since a wrong ID or redirect can yield a different game.

### Gemini Web-Search Quota Discipline (current free-tier project)
- Keep `plugins.entries.google.config.webSearch.model` on **`gemini-2.5-flash`**. This project has usable Google Search grounding for the Gemini 2.5 family (1,500 requests/day); Gemini 3/3.5/3.6 grounding shows 0 quota, so do not switch to them unless the user confirms their quota has changed.
- Standard Gemini 2.5 Flash limits observed in Google AI Studio: **5 RPM**, **250k TPM**, and **20 RPD**. Treat these as project/tier-specific and re-check the Google AI Studio quota page if they matter to a task.
- Use one focused search first. Do not launch large parallel batches (especially 4+ calls); they can waste the 20 daily model requests and trigger the 5 RPM cap. Parallelize only truly independent, high-value queries and keep the batch to 2–3 calls.
- Space sequential Gemini searches by at least **15 seconds**. If a rate-limit error occurs, pause for **60 seconds** before one retry; reduce fan-out and use official `web_fetch` pages/APIs for follow-up verification rather than more search calls.
- Search is for discovery; use `web_fetch` on primary sources for precise facts. Its HTTP fetches do not require an additional Gemini-grounding query.
- **Default decision workflow:** make exactly **one focused, serial Gemini search** to discover sources; then verify price, availability, specs, policy, or release claims through the manufacturer or an authorised/local retailer using `web_fetch`. Never promote a Gemini summary, SEO aggregator, marketplace listing, or rumour into an “official” fact. State the source type and uncertainty when verification is incomplete.
- **Burst protection:** do not run Gemini searches concurrently unless the user explicitly needs independent research. Treat every search as chargeable against the project quota. Prefer one broad-enough query, then fetch sources; do not repeat a query merely because its summary is weak.

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
