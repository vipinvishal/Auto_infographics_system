# 🖼️ VipinAIHub Daily Infographic Agent

> Every day, GitHub Actions finds a trending **AI / GenAI / Agentic-AI** topic, turns it into one branded hand-drawn-style infographic PNG, writes a copy-paste caption, and emails both to you. No server, no manual work.

Built on the same architecture as [Auto-carousel-agent](https://github.com/vipinvishal/Auto-carousel-agent), adapted to produce a **single educational infographic** instead of an 8-slide carousel.

---

## Pipeline

```
GitHub Actions cron (daily 06:30 IST)
        │
   check_trends.py ── dedup vs last_story.txt
        │
   trends.py        (HN + Reddit, AI/GenAI/Agentic only — free)
        │
   scraper.py       (article text, HN-comments fallback)
        │
   content_api.py   (OpenRouter → reframe into a 3-stage explainer → schema JSON)
        │
   renderer/render.py  (Playwright → 1800px branded PNG)
        │
   caption_api.py   (OpenRouter → writeup + hashtags)
        │
   emailer.py       (Gmail SMTP → vipinislearning@gmail.com)
```

## Why "hybrid" discovery
Hacker News + Reddit tell us what's hot in AI **right now** (free, no key). The LLM
then reframes that news into an **evergreen "how it works in 3 stages"** concept that
fits the infographic template — so you get a current-but-teachable topic every day,
never plain cloud/devops.

## Files

| File | Job |
|---|---|
| `check_trends.py` | Entry point (run by Actions): discover + dedup → pipeline |
| `agent.py` | Orchestrator: content → render → writeup → email |
| `trends.py` | HN + Reddit AI-story discovery (keyword-filtered) |
| `scraper.py` | Article text + HN-comments fallback |
| `openrouter_client.py` | Thin OpenRouter (OpenAI-compatible) wrapper |
| `content_api.py` | Story → infographic schema JSON (validated, retried) |
| `caption_api.py` | Topic → writeup + per-platform hashtags |
| `emailer.py` | Gmail SMTP, PNG as downloadable attachment |
| `config.py` | Keys (env), models per step, brand constants |
| `renderer/` | Existing infographic system (render.py + template + fonts + portrait) |
| `last_story.txt` | Dedup memory, committed back each run |
| `.github/workflows/daily.yml` | Daily cron + manual trigger |

## Setup

### 1. Install
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Keys
| Key | Where |
|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `GMAIL_APP_PASSWORD` | Google Account → Security → 2-FA → [App Passwords](https://myaccount.google.com/apppasswords) |

```bash
cp .env.example .env   # fill in both keys
```

### 3. Run
```bash
python agent.py         # test the pipeline with a built-in sample story
python check_trends.py  # full run: discover → render → email
```

## GitHub Actions (daily automation)
1. Push this repo to GitHub.
2. Repo → **Settings → Secrets and variables → Actions** → add:
   - `OPENROUTER_API_KEY`
   - `GMAIL_APP_PASSWORD`
3. The workflow runs daily at **06:30 IST** (`0 1 * * *` UTC) and has a manual
   **Run workflow** button. Each run commits `last_story.txt` back so topics never repeat.

## Change models
Edit `config.py` (or set env vars). Append `:online` to any model id to enable
OpenRouter web search, e.g. `CONTENT_MODEL=google/gemini-2.0-flash-001:online`.

## Brand
VipinAIHub · @VipinAIHub · x.com/VipinAIHub · linkedin.com/in/vipin-vishal-b8b92643

## License
MIT — fork and adapt for your own brand.
