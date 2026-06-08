"""
config.py — All keys, constants, and settings for the daily infographic agent.

Sensitive values come from environment variables; never hardcode secrets.
For local dev, create a .env file in the project root:

  OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

(Mirrors the config.py pattern from the Auto-carousel-agent reference repo.)
"""

import os
from pathlib import Path

# Load .env if present (harmless in CI where vars are set natively)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed — rely on shell env vars

ROOT = Path(__file__).parent

# ── OpenRouter (one key → Gemini, Grok, etc.) ──────────────────────────────
# Get a key at https://openrouter.ai/keys . OpenRouter is OpenAI-compatible.
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

# Model per pipeline step. Swap these strings to change models — no code change.
#   * append ":online" to ANY model to turn on OpenRouter web search.
#   * DISCOVERY model reframes a trending story into an evergreen explainer.
DISCOVERY_MODEL: str = os.environ.get("DISCOVERY_MODEL", "x-ai/grok-4.3")
CONTENT_MODEL:   str = os.environ.get("CONTENT_MODEL",   "google/gemini-2.5-flash")
CAPTION_MODEL:   str = os.environ.get("CAPTION_MODEL",   "google/gemini-2.5-flash")

# Optional headers OpenRouter uses for attribution / rankings.
OPENROUTER_REFERER: str = "https://github.com/vipinvishal"
OPENROUTER_TITLE:   str = "VipinAIHub Daily Infographic Agent"

# ── Gmail SMTP ─────────────────────────────────────────────────────────────
GMAIL_USER: str = "vipinislearning@gmail.com"
GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL: str = "vipinislearning@gmail.com"

# ── Brand ──────────────────────────────────────────────────────────────────
BRAND_NAME: str = "VipinAIHub"
BRAND_HANDLE: str = "@VipinAIHub"
BRAND_X: str = "x.com/VipinAIHub"
BRAND_LINKEDIN: str = "linkedin.com/in/vipin-vishal-b8b92643"
BRAND_EMAIL: str = "vipinislearning@gmail.com"

# ── Renderer (your existing Playwright infographic system) ─────────────────
RENDERER_DIR = ROOT / "renderer"
ICON_NAMES = [
    "upload", "laptop", "copies", "database", "lock",
    "cloud", "gear", "file", "search", "key", "network",
]

# ── Output / dedup ─────────────────────────────────────────────────────────
OUTPUT_DIR: str = "output"
LAST_STORY_FILE: str = "last_story.txt"
