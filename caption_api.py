"""
caption_api.py — Generate a copy-paste writeup + hashtags for the infographic.

Second OpenRouter call. Produces a Hinglish-leaning caption tuned for Instagram /
LinkedIn / Threads, plus a short explainer paragraph — all plain text the user
pastes straight into the email/post.
"""

import logging

import config
import openrouter_client as orc

logger = logging.getLogger(__name__)

_SYSTEM = """You write social captions for @VipinAIHub, an AI-education creator.
Write in ENGLISH ONLY — clear, simple, conversational English. Do NOT use Hindi,
Hinglish, or any other language. Tone: a smart friend explaining AI, zero corporate
filler. Return plain text only — the exact words to copy-paste. No JSON, no preamble."""

_USER_TEMPLATE = """The infographic explains this AI concept: "{topic}"

Key points covered:
{points}

Write the following sections, separated by lines of "---", in THIS order:

INSTAGRAM
A scroll-stopping caption. Open with a hook line, then 2-3 punchy facts as
numbered points, end with a question to drive comments. Then a blank line, then
8-12 relevant hashtags including #VipinAIHub #AI #GenAI #AgenticAI.

LINKEDIN
A slightly more professional 3-4 line version of the same idea (still human, no
buzzwords), ending with a soft CTA to follow. Then 5-7 hashtags.

THREADS
One tight, punchy 1-2 line take. No hashtags.

Keep it tight. Do not add any other commentary."""


def get_caption(content: dict) -> str:
    topic = content.get("topic", "an AI concept")
    points = []
    for st in content.get("stages", []):
        if st.get("title"):
            points.append(f"- {st['title']}: {st.get('subtitle', '')}")
    for ex in content.get("explainers", []):
        if ex.get("tag"):
            # strip simple html tags for the prompt
            body = ex.get("body", "")
            for t in ("<b>", "</b>", "<span class='k1'>", "<span class='k2'>",
                      "<span class='k3'>", "<span class='n'>", "<span class='h'>", "</span>"):
                body = body.replace(t, "")
            points.append(f"- {ex['tag']}: {body}")
    points_text = "\n".join(points) or topic

    prompt = _USER_TEMPLATE.format(topic=topic, points=points_text)
    try:
        text = orc.chat(
            model=config.CAPTION_MODEL,
            system=_SYSTEM,
            user=prompt,
            temperature=0.7,
            max_tokens=900,
        )
        logger.info("Caption generated — %d chars", len(text))
        return text
    except RuntimeError as exc:
        logger.warning("Caption generation failed: %s", exc)
        return f"{topic}\n\n#VipinAIHub #AI #GenAI #AgenticAI"
