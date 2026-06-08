"""
scraper.py — Pull readable article text from a story URL.

Strategy:
  1. If the story already has self-text (Reddit), use it.
  2. Otherwise fetch the URL and extract <p> / <article> text via BeautifulSoup.
  3. HN fallback: scrape top comments (often more insightful than the article).

Returns plain text (caller truncates). Empty string on failure — the pipeline
then falls back to the headline alone.
"""

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_MAX_CHARS = 6000


def scrape_article(url: str, selftext: str = "") -> str:
    if selftext and len(selftext.strip()) > 120:
        logger.info("Using Reddit self-text (%d chars).", len(selftext))
        return selftext.strip()[:_MAX_CHARS]

    if not url or "news.ycombinator.com" in url:
        return ""

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Article fetch failed (%s): %s", url, exc)
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    article = soup.find("article")
    container = article if article else soup
    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 40)

    if len(text) < 200:
        logger.info("Sparse article text (%d chars).", len(text))
        return text[:_MAX_CHARS]

    logger.info("Scraped %d chars from %s", len(text), url)
    return text[:_MAX_CHARS]


def scrape_hn_comments(story_id: str, max_comments: int = 8) -> str:
    """Fetch the top comments of an HN story as fallback context."""
    try:
        item = requests.get(f"{_HN_BASE}/item/{story_id}.json", timeout=10).json()
    except Exception as exc:
        logger.warning("HN item fetch failed: %s", exc)
        return ""

    kids = (item or {}).get("kids", [])[:max_comments]
    texts = []
    for kid in kids:
        try:
            c = requests.get(f"{_HN_BASE}/item/{kid}.json", timeout=8).json()
            if c and c.get("text"):
                texts.append(BeautifulSoup(c["text"], "html.parser").get_text(" ", strip=True))
        except Exception:
            continue

    joined = "\n\n".join(texts)
    logger.info("HN comments fallback: %d chars from %d comments", len(joined), len(texts))
    return joined[:_MAX_CHARS]
