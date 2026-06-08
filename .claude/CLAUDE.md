# VipinAIHub Daily Infographic Agent

## What This Project Does
Every day a GitHub Actions cron job:
1. Scans Hacker News + Reddit for a trending **AI / GenAI / Agentic-AI** story (free, no key)
2. Reframes it (via OpenRouter LLM) into an evergreen "how it works in 3 stages" concept
3. Fills the infographic content schema → validated JSON
4. Renders one branded PNG via the existing Playwright renderer (`renderer/`)
5. Generates a copy-paste writeup + hashtags (IG / LinkedIn / Threads)
6. Emails the PNG + writeup to vipinislearning@gmail.com via Gmail SMTP

No server. Open the email, copy the writeup, post the image.

## Tech Stack
- Runtime: Python 3.11+
- Scheduler: GitHub Actions cron (`.github/workflows/daily.yml`)
- Discovery: Hacker News API + Reddit JSON API (free)
- AI: OpenRouter (OpenAI-compatible) — Grok for reframe, Gemini for content/caption
- Render: Playwright + Jinja2 (HTML → 1800px PNG), fonts base64-embedded
- Email: Gmail SMTP (App Password)

## Architecture (mirrors the Auto-carousel-agent reference repo)
- `check_trends.py` — entry point: discover + dedup, then call the pipeline
- `agent.py` — orchestrator: content → render → writeup → email
- `trends.py` — HN + Reddit AI-story discovery (keyword-filtered to AI/GenAI/Agentic)
- `scraper.py` — article text + HN-comments fallback
- `openrouter_client.py` — thin OpenAI-compatible OpenRouter wrapper
- `content_api.py` — story → infographic schema JSON (validated, retried)
- `caption_api.py` — topic → writeup + hashtags
- `emailer.py` — Gmail SMTP, PNG as downloadable attachment
- `config.py` — keys (env), models, brand constants
- `renderer/` — the existing infographic system (render.py + template + fonts + portrait)
- `last_story.txt` — dedup memory, committed back each run

## Topic Rule
Topics MUST be about Artificial Intelligence, Generative AI, or Agentic AI only.
Enforced in `trends.py` keyword filter AND the `content_api.py` system prompt.

## Brand Config
- Brand: VipinAIHub  ·  Handle: @VipinAIHub
- Email: vipinislearning@gmail.com
- X: x.com/VipinAIHub  ·  LinkedIn: linkedin.com/in/vipin-vishal-b8b92643

## Key Rules
- Never hardcode API keys — always via `config.py` / env vars
- Content JSON must match `renderer/data/sample_content.json` schema exactly
- Exactly 3 stages + 3 explainers; last stage `arrow_note` is ""
- stage.icon ∈ {upload, laptop, copies, database, lock, cloud, gear, file, search, key, network}
- Email subject: "🖼️ Daily Infographic — {topic}"; body = writeup ready to copy

## Environment Variables (GitHub Actions secrets)
- `OPENROUTER_API_KEY`
- `GMAIL_APP_PASSWORD`

## Local Dev
    pip install -r requirements.txt
    playwright install chromium
    cp .env.example .env   # fill in keys
    python agent.py        # test pipeline with a built-in sample story
    python check_trends.py # full run: discover → … → email
