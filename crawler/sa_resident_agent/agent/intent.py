"""
sa_resident_agent/agent/intent.py

Classifies a user message into one of three intents using the LLM.
Falls back to QUESTION on any failure.
"""

from __future__ import annotations

import logging
from enum import Enum

from sa_resident_agent.llm.utsa_client import UTSAClient

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    QUESTION   = "QUESTION"    # asking about rates, docs, policies
    FORM_HELP  = "FORM_HELP"   # filling a form, needs field guidance
    STATUS     = "STATUS"      # asking about their own checklist progress


INTENT_SYSTEM_PROMPT = """You are an intent classifier for a utility enrollment assistant.
Classify the user message into exactly one of: QUESTION, FORM_HELP, STATUS.

Definitions:
- QUESTION   : User is asking about rates, policies, required documents, deadlines, or general info about CPS Energy, SAWS, or the City of San Antonio.
- FORM_HELP  : User is filling out a form or needs help with a specific form field (e.g. "what do I put for service address?").
- STATUS     : User is asking about their own setup progress or checklist (e.g. "what have I completed?", "what's left?").

Respond with ONLY the label — no explanation, no punctuation."""


def classify_intent(message: str, llm: UTSAClient) -> Intent:
    """
    Classify the user message. Returns an Intent enum value.
    Falls back to Intent.QUESTION on any LLM error.
    """
    if not message.strip():
        return Intent.QUESTION

    messages = [
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {"role": "user",   "content": message.strip()},
    ]

    try:
        raw = llm.chat(messages, temperature=0.0, max_tokens=10).strip().upper()
        # Strip any accidental punctuation
        raw = raw.strip(".,!? \n")

        if raw in Intent._value2member_map_:
            return Intent(raw)

        logger.warning(f"Unexpected intent label '{raw}' — defaulting to QUESTION")
        return Intent.QUESTION

    except Exception as e:
        logger.warning(f"Intent classification failed: {e} — defaulting to QUESTION")
        return Intent.QUESTION
