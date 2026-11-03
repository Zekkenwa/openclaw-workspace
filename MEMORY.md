# Memory Export — Raihan
*Exported from Claude (Anthropic) on 2026-08-12. Derived from prior conversations; not guaranteed complete or fully current.*

## Identity
- Name: Raihan
- GitHub: Zekkenwa
- MyAnimeList: rfa-chan
- Location: Depok/Bekasi area, Indonesia
- Primary language: Casual Indonesian with English code-switching

## Education
- Diploma in Mechanical Engineering (Design focus), Politeknik Negeri Jakarta (PNJ) — entered via SM-KPN track after earlier university attempts didn't pan out
- BNSP Mechanical Maintenance Technology certification
- TOEFL ITP score: 557
- JLPT N5: passed, July 2026
- JLPT N4: passive self-study in progress, using Genki I, no fixed exam date

## Work — Current
- Staff Engineer (Contract), PT Sarana Utama Adimandiri (PT SUA) — started July 2026
- M&E construction contractor; clients include Takenaka, Sumitomo Mitsui Construction, Toyota Motor Manufacturing Indonesia
- Scope: pipe sizing, material selection, pump calculations, quantity takeoffs (PlanSwift), HVAC/drainage design, Excel-based engineering tools
- Standards in use: SHASE-S 206, SNI 8153:2015 (drainage), JIS/SMACNA/ASHRAE (HVAC ducting)
- Built: Excel DFU drainage calculators (multi-branch, SHASE-S 206 tables), Hazen-Williams pipe sizing workbook with SNI fittings tables, interactive HTML tools for duct sizing (Colebrook-White, Huebscher equivalent diameter)
- Also handled: cooling water flushing commissioning, PPR piping BOQ work, Japanese-standard terminology (SW/WW, osui/zappaisui)

## Work — Prior
- Drafter, PT Putra Karya Teknik (Feb–Jul 2026) — technical drawings in Autodesk Inventor/Fusion 360 (shafts, snap rings, gears, bearings, custom fittings); client part ID and thread measurement
- Internship, PLN Indonesia Power (Feb–May 2025) — per-second sensor data logging for efficiency analysis
- Considered the Tokutei Ginou Japan work program via PNJ's P2BJ; decided to wait for a future batch
- Also screened for PT Monokem Surya (Engineering Support Intern)

## Public Projects
- Kasaku — WhatsApp cashflow bot, TypeScript
- inventor-discord-rpc — Python
- Private repos: dlmusic, MALTOANILISTSYNC
- Academic: 1-Ton Jib Crane, PEDC-06 Nano Carbon Machine

## Interests / Hobbies
- Runs 5K regularly, tracks via Strava
- Games: Valorant, Zenless Zone Zero, Ghost of Tsushima
- Anime: 114+ days watched, mean score 7.8
- Hololive fan — especially Suisei (music), regularly watches Polka, Ollie, Okayu, Miko, Roboco, Zeta, Shiori, Bae

## Active Projects / Top of Mind
- ~~RTX 4060 eGPU build~~ DISCONTINUED (Oct 2026) — judged not worth the effort/price; now planning to buy a desktop PC instead. GPU research in progress: RX 6600 vs 6600 XT for 1440p (RX 6700 XT suggested as better 1440p value)
- Troubleshot yt-dlp SSL/TLS issues on Windows/Git Bash; resolved YouTube download failures via VPN
- Ran a pip package audit — 34 outdated packages identified
- Selling: Leica DISTO D5, ADATA SU650 SSD (received as gift)
- Dual-boot Windows/Ubuntu setup; MacBuntu GNOME 50 environment (user: zekkenwa, host: rfaslenovo); tools used include ani-cli, yt-dlp, Vencord/Vesktop, ReVanced, Termux

## Working Style / Preferences (as expressed to Claude)
- Prefers direct, critical, source-grounded answers over hedged or generic advice
- Pushes back on imprecise answers or unverified assumptions
- Prefers metric units
- Works at an engineering company — comfortable with and expects critical feedback

## Lessons Learned — Tool System

### Deferred Tools via `tool_call` (2026-10-22)
**Mistake:** Passed `{"reason": "..."}` in the `args` object when calling deferred tools like `dashboard` through `tool_call`. The wrapper passes `args` directly to the target tool, which has its own strict schema (e.g., `dashboard` requires `action`, doesn't accept arbitrary fields).

**Correct usage:**
1. Use `tool_search` or `tool_describe` first if the schema isn't clear.
2. Pass only the target tool's documented parameters in `args`: dashboard → `{"action":"read"}`; web search → `{"query":"...","count":5}`.
3. Never substitute a narrative `reason` for a required field such as `query` or `action`.
4. After one schema failure, compare the submitted payload with the validator's required schema and materially correct it. After a second validation failure, stop retries, inspect the full schema, and make one corrected call or report the blocker.
