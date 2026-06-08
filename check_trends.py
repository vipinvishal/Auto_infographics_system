"""
check_trends.py — Entry point run by GitHub Actions (daily cron).

1. Fetch the top trending AI / GenAI / Agentic story (HN + Reddit, free).
2. Skip stories already processed recently (dedup via last_story.txt).
3. Scrape article text (HN-comments fallback).
4. Run the infographic pipeline (content → render → writeup → email).
5. On success, record the story id so the next run won't repeat it.
"""

import logging
import os
import sys

import config
import scraper
import trends
from agent import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


TOPICS_FILE = "topics_history.txt"


def _read_lines(path: str) -> list[str]:
    if os.path.exists(path):
        return [ln.strip() for ln in open(path, encoding="utf-8") if ln.strip()]
    return []


def _recent_ids() -> list[str]:
    return _read_lines(config.LAST_STORY_FILE)


def _recent_topics() -> list[str]:
    return _read_lines(TOPICS_FILE)


def _record_id(story_id: str, keep: int = 300) -> None:
    ids = _recent_ids() + [story_id]
    with open(config.LAST_STORY_FILE, "w") as fh:
        fh.write("\n".join(ids[-keep:]) + "\n")
    logger.info("Recorded story id: %s", story_id)


def _record_topic(topic: str, keep: int = 200) -> None:
    topics = _recent_topics() + [topic]
    with open(TOPICS_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(topics[-keep:]) + "\n")
    logger.info("Recorded topic: %s", topic)


def main() -> int:
    logger.info("=== VipinAIHub Infographic Agent — Daily Run ===")

    seen = set(_recent_ids())
    stories = trends.get_top_stories(15)
    if not stories:
        logger.error("No AI stories found in the last 48 hours. Exiting.")
        return 1

    story = next((s for s in stories if s["id"] not in seen), None)
    if story is None:
        logger.info("All top stories already processed. Nothing new today. ✓")
        return 0

    logger.info("Selected [%s | score=%d]: %s",
                story["source"], story["score"], story["title"])

    article_text = scraper.scrape_article(story["url"], story.get("selftext", ""))
    if not article_text and story["source"] == "hackernews":
        logger.info("Article scrape empty — falling back to HN comments …")
        article_text = scraper.scrape_hn_comments(story["id"])
    if not article_text:
        logger.warning("No article text — using headline only.")
        article_text = f"Trending AI topic: {story['title']}\nSource: {story['url']}"

    # Last 40 covered concepts steer the LLM away from repeats.
    avoid_topics = _recent_topics()[-40:]
    result = run_pipeline(article_text, story["title"],
                          source=story["source"], avoid_topics=avoid_topics)
    if result["success"]:
        _record_id(story["id"])
        _record_topic(result["topic"])
        logger.info("Done. Email sent: %s", result["email_sent"])
        return 0

    logger.error("Pipeline failed: %s", result["error"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
