"""
agent.py — Core pipeline orchestrator.

Pipeline:
  1. Generate infographic content from a story   (content_api.py → OpenRouter)
  2. Render the branded PNG                       (renderer/render.py → Playwright)
  3. Generate the copy-paste writeup              (caption_api.py → OpenRouter)
  4. Email the PNG + writeup                       (emailer.py → Gmail SMTP)

Run directly to test with a built-in sample story (no trends fetch):
  python agent.py
  python agent.py "article text here" "Story title"
"""

import json
import logging
import os
import re
import sys
from datetime import datetime

import caption_api
import config
import content_api
import emailer

# Make the renderer importable (it uses paths relative to its own dir).
sys.path.insert(0, str(config.RENDERER_DIR))
import render  # noqa: E402  (renderer/render.py)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_TEST_TEXT = (
    "A new open-source framework lets LLM agents plan, call tools, observe the "
    "result, and loop until the task is done. It uses a ReAct-style reason-act "
    "cycle: the model emits a thought, picks a tool, reads the observation, then "
    "decides the next step. Benchmarks show multi-step task success jumps when "
    "the agent can retry failed tool calls and keep short-term memory of prior steps."
)
_TEST_TITLE = "New ReAct-style agent framework loops tools until the task is solved"


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    return slug[:max_len] or "infographic"


def run_pipeline(article_text: str, topic_title: str, source: str = "",
                 avoid_topics: list[str] | None = None) -> dict:
    result = {
        "success": False, "topic": topic_title, "output_dir": "",
        "png_path": "", "email_sent": False, "error": None,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(config.OUTPUT_DIR, f"{_slugify(topic_title)}_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)
    result["output_dir"] = out_dir

    # 1. Content JSON
    logger.info("[1/4] Generating infographic content via OpenRouter …")
    try:
        content = content_api.get_content(article_text, topic_title, source, avoid_topics)
    except RuntimeError as exc:
        result["error"] = f"Content generation failed: {exc}"
        logger.error(result["error"])
        return result

    result["topic"] = content.get("topic", topic_title)
    content_path = os.path.join(out_dir, "content.json")
    with open(content_path, "w") as fh:
        json.dump(content, fh, indent=2, ensure_ascii=False)

    # 2. Render PNG
    logger.info("[2/4] Rendering PNG via Playwright …")
    png_path = os.path.join(out_dir, "infographic.png")
    try:
        render.render(content_path, png_path)
    except Exception as exc:
        result["error"] = f"Render failed: {exc}"
        logger.error(result["error"])
        return result
    result["png_path"] = png_path

    # 3. Writeup
    logger.info("[3/4] Generating writeup + hashtags …")
    caption = caption_api.get_caption(content)
    with open(os.path.join(out_dir, "writeup.txt"), "w") as fh:
        fh.write(caption)

    # 4. Email
    logger.info("[4/4] Emailing PNG + writeup …")
    result["email_sent"] = emailer.send_infographic_email(
        png_path, result["topic"], caption, content,
    )

    result["success"] = True
    logger.info("Pipeline complete — topic='%s' email_sent=%s out=%s",
                result["topic"], result["email_sent"], out_dir)
    return result


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else _TEST_TEXT
    title = sys.argv[2] if len(sys.argv) > 2 else _TEST_TITLE

    logger.info("=== VipinAIHub Infographic Agent — Test Run ===")
    res = run_pipeline(text, title, source="test")

    print("\n" + "=" * 60 + "\nRESULT\n" + "=" * 60)
    for k, v in res.items():
        print(f"  {k}: {v}")
    print("=" * 60)
    sys.exit(0 if res["success"] else 1)
