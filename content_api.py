"""
content_api.py — Turn a trending AI story into INFOGRAPHIC content JSON.

Hybrid approach: the trending story (from HN/Reddit) gives us what's hot RIGHT
NOW in AI; the LLM reframes it into an evergreen "how X works in N stages"
explainer that fits the infographic template, then fills every schema slot.

Output matches renderer/data/sample_content.json exactly, so render.py can draw
it with zero manual edits. We validate + nudge field lengths and icon names;
render.py's auto-fit pass catches any remaining overflow.
"""

import json
import logging

import config
import openrouter_client as orc

logger = logging.getLogger(__name__)

# Icons the renderer ships with (renderer/icons.py).
_ICONS = ", ".join(config.ICON_NAMES)

_SYSTEM = """You are an AI/Tech educator who designs single-image explainer infographics.
You take a trending AI / Generative-AI / Agentic-AI story and reframe it into ONE
evergreen "how it works" concept that can be explained in exactly 3 visual stages.
You ONLY cover Artificial Intelligence, Generative AI, or Agentic AI — never plain
cloud, devops, or unrelated tech. You return valid JSON only: no markdown, no prose."""

_USER_TEMPLATE = """TRENDING AI STORY (your inspiration, not the literal subject):
Title: "{title}"
Source: {source}

ARTICLE / CONTEXT:
{article}

---

TASK
Reframe this into ONE evergreen, teachable AI concept that fits a 3-stage
"how it works" infographic for @VipinAIHub. Prefer the underlying mechanism over
the news headline (e.g. a story about a new agent framework → "How an AI Agent
Decides Its Next Action"; a story about RAG → "How RAG Answers Your Question").

HARD RULES
- Topic MUST be about AI, Generative AI, or Agentic AI. Nothing else.
- EXACTLY 3 stages and EXACTLY 3 explainers.
- Every value concrete and specific — no filler like "AI is powerful".
- stage.title <= 22 characters. stage.subtitle <= 30 characters, one line.
- stage.icon MUST be one of: {icons}
- arrow_note is a tiny 1-3 word label; the LAST stage's arrow_note MUST be "".
- explainer.body may use <span class='k1'>..</span>, <span class='k2'>..</span>,
  <span class='k3'>..</span> to highlight a key term, and <b>..</b> for bold.
- quote_main may use <span class='n'>NUMBER</span> and <span class='h'>highlight</span>.
- handle MUST be exactly "@VipinAIHub".
- terminal_cmd is a short, real-looking shell/CLI line, <= 18 chars, ideally
  one token (e.g. "agent.run()", "rag.query()", "aws s3 cp"). No long arguments.
- sticky1 and sticky2 are <= 7 words each.

Return a single JSON object with EXACTLY these keys:
{{
  "topic": "the evergreen concept title, plain text",
  "headline_line1_pre": "text before the highlighted word, e.g. 'How '",
  "headline_line1_hl": "the ONE highlighted word, e.g. 'RAG'",
  "headline_line1_post": "text after it on line 1 (may be empty)",
  "headline_line2": "the second headline line (blue)",
  "sub_pre": "short lead, e.g. 'A Query Travels Through'",
  "sub_num": "3",
  "sub_post": "e.g. 'Stages'",
  "stages": [
    {{"title": "<=22 chars", "subtitle": "<=30 chars", "icon": "one of the icons", "arrow_note": "1-3 words"}},
    {{"title": "<=22 chars", "subtitle": "<=30 chars", "icon": "one of the icons", "arrow_note": "1-3 words"}},
    {{"title": "<=22 chars", "subtitle": "<=30 chars", "icon": "one of the icons", "arrow_note": ""}}
  ],
  "explainers": [
    {{"tag": "short heading", "body": "1-2 sentences, may use <span class='k1'> and <b>"}},
    {{"tag": "short heading", "body": "1-2 sentences, may use <span class='k2'> and <b>"}},
    {{"tag": "short heading", "body": "1-2 sentences, may use <span class='k3'> and <b>"}}
  ],
  "sticky1": "short aha note, use <b> for the key word",
  "terminal_cmd": "short CLI command",
  "sticky2": "short aha note, use <b> for the key word",
  "quote_main": "a punchy fact, use <span class='n'> for a number and <span class='h'> for highlight",
  "quote_sub": "one supporting line",
  "handle": "@VipinAIHub"
}}"""

_REQUIRED_KEYS = [
    "topic", "headline_line1_pre", "headline_line1_hl", "headline_line1_post",
    "headline_line2", "sub_pre", "sub_num", "sub_post", "stages", "explainers",
    "sticky1", "terminal_cmd", "sticky2", "quote_main", "quote_sub", "handle",
]


def _parse_json(raw: str) -> dict:
    cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def _coerce(data: dict) -> dict:
    """Fix structural issues so render.py never crashes."""
    # Stages → exactly 3 well-formed dicts
    stages = data.get("stages") or []
    while len(stages) < 3:
        stages.append({"title": "", "subtitle": "", "icon": "file", "arrow_note": ""})
    stages = stages[:3]
    for i, st in enumerate(stages):
        st.setdefault("title", "")
        st.setdefault("subtitle", "")
        icon = st.get("icon", "file")
        st["icon"] = icon if icon in config.ICON_NAMES else "file"
        st["arrow_note"] = "" if i == 2 else st.get("arrow_note", "")
    data["stages"] = stages

    # Explainers → exactly 3
    exps = data.get("explainers") or []
    while len(exps) < 3:
        exps.append({"tag": "", "body": ""})
    for ex in exps:
        ex.setdefault("tag", "")
        ex.setdefault("body", "")
    data["explainers"] = exps[:3]

    # Required scalars
    data["sub_num"] = str(data.get("sub_num", "3"))
    data["handle"] = "@VipinAIHub"
    for key in _REQUIRED_KEYS:
        if key not in data:
            data[key] = "" if key not in ("stages", "explainers") else data[key]
    return data


def get_content(article_text: str, topic_title: str, source: str = "") -> dict:
    """Generate validated infographic content JSON from a story."""
    article = (article_text or "").strip()[:5500] or topic_title
    prompt = _USER_TEMPLATE.format(
        title=topic_title, source=source, article=article, icons=_ICONS,
    )

    last_err = ""
    for attempt in range(1, 3):  # one retry
        try:
            raw = orc.chat(
                model=config.CONTENT_MODEL,
                system=_SYSTEM,
                user=prompt if attempt == 1 else prompt + f"\n\nPREVIOUS ATTEMPT FAILED: {last_err}\nReturn corrected JSON only.",
                json_mode=True,
                temperature=0.45,
                max_tokens=2048,
            )
            data = _coerce(_parse_json(raw))
            logger.info("Content generated — topic: %s", data.get("topic", "?"))
            return data
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            logger.warning("Content parse failed (attempt %d): %s", attempt, last_err)

    raise RuntimeError(f"Content generation failed after retries: {last_err}")
