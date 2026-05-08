"""
sa_resident_agent/agent/agent.py

Main agent orchestrator.

In simulate_mode=True:
- Skips intent classification and RAG
- Extracts field values from LLM replies using keyword matching
- Injects ALL collected fields into every prompt turn (prevents LLM amnesia)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from sa_resident_agent.agent.context import ContextManager
from sa_resident_agent.agent.intent import Intent, classify_intent
from sa_resident_agent.agent.prompts import (
    build_form_help_prompt,
    build_question_prompt,
    build_simulate_prompt,
    build_status_prompt,
)
from sa_resident_agent.knowledge.retriever import Retriever
from sa_resident_agent.knowledge.vector_store import RetrievedChunk
from sa_resident_agent.llm.utsa_client import LLMUnavailableError, UTSAClient

logger = logging.getLogger(__name__)

PROVIDER_KEYWORDS: dict[str, list[str]] = {
    "CPS_ENERGY": ["cps", "electric", "electricity", "power", "energy", "kwh", "light bill"],
    "SAWS":       ["saws", "water", "sewer", "sewage", "wastewater"],
    "CITY_SA":    ["city", "san antonio", "permit", "registration", "municipal", "311", "trash", "garbage"],
}

TOP_K = 5
SCORE_THRESHOLD = 0.55

# Maps phrases the LLM says when confirming a field to the field key we store
# Format: (phrase_in_reply, field_key)
FIELD_CONFIRMATION_PATTERNS = [
    # CPS fields
    (r"your (?:full legal )?name is (.+?)[\.\n]",                    "cps_name"),
    (r"service address is (.+?)[\.\n]",                              "cps_service_address"),
    (r"mailing address is (?:the same|(.+?))[\.\n]",                 "cps_mailing_same"),
    (r"move.in date is (.+?)[\.\n]",                                 "cps_move_in_date"),
    (r"texas driver.?s? license(?: number)? is (.+?)[\.\n]",         "cps_id_number"),
    (r"(?:id type|identification).+?(?:texas driver|state id|ssn|social|federal)",  "cps_id_type"),
    (r"phone number is (.+?)[\.\n]",                                 "cps_phone"),
    (r"email address is (.+?)[\.\n]",                                "cps_email"),
    (r"prefer to pay.+?(autopay|online|in person|by phone)",         "cps_payment"),
    (r"(?:first time|not your first time)",                          "cps_new_customer"),
    (r"(?:enroll in paperless|not.*paperless|paperless billing)",     "cps_paperless"),
    # SAWS fields
    (r"saws.+?account type.+?(single.family|apartment|condo)",       "saws_account_type"),
    (r"(?:pay the deposit|deposit waiver|saws deposit)",             "saws_deposit"),
    (r"(?:saws autopay|autopay for saws)",                           "saws_autopay"),
    # City fields
    (r"garbage pickup day.+?(monday|tuesday|wednesday|thursday|friday)", "city_garbage_day"),
    (r"recycling cart.+?(?:35|65|95).gallon",                        "city_recycling_cart"),
    (r"(?:bulk item|bulk pickup)",                                   "city_bulk_pickup"),
    (r"(?:311 account|sa311)",                                       "city_311_account"),
    (r"(?:parking permit)",                                          "city_parking_permit"),
]


@dataclass
class SourceDoc:
    url: str
    provider: str
    chunk_preview: str


@dataclass
class AgentResponse:
    session_id: str
    reply: str
    intent: str
    sources: list[SourceDoc] = field(default_factory=list)
    checklist: dict[str, str] = field(default_factory=dict)
    error: str | None = None


class Agent:
    def __init__(
        self,
        chroma_path: str = "data/chroma",
        llm: UTSAClient | None = None,
        simulate_mode: bool = False,
    ):
        self.retriever     = Retriever(persist_path=chroma_path)
        self.llm           = llm or UTSAClient()
        self.context       = ContextManager()
        self.simulate_mode = simulate_mode

    def chat(self, session_id: str, message: str) -> AgentResponse:
        message = message.strip()
        if not message:
            return AgentResponse(
                session_id=session_id,
                reply="Please enter a message.",
                intent=Intent.QUESTION,
                checklist=self.context.get_checklist(session_id),
                error="empty_message",
            )

        # ── SIMULATE MODE ──────────────────────────────────────────────
        if self.simulate_mode:
            history          = self.context.get_history(session_id)
            collected_fields = self.context.get_collected_fields(session_id)

            messages = build_simulate_prompt(message, history, collected_fields)

            try:
                reply = self.llm.chat(messages, max_tokens=1024)
            except LLMUnavailableError as e:
                logger.error(f"LLM unavailable: {e}")
                return AgentResponse(
                    session_id=session_id,
                    reply="I'm having trouble reaching the language model. Please check your UTSA network connection.",
                    intent="SIMULATE",
                    checklist=self.context.get_checklist(session_id),
                    error="llm_unavailable",
                )

            # Extract confirmed field values from the reply
            self._extract_fields_from_reply(session_id, reply, message)

            # Update checklist based on completion markers
            reply_lower = reply.lower()
            if "cps energy enrollment complete" in reply_lower:
                self.context.mark_complete(session_id, "CPS_ENERGY")
            elif any(k.startswith("cps_") for k in self.context.get_collected_fields(session_id)):
                self.context.advance_checklist(session_id, "CPS_ENERGY")

            if "saws enrollment complete" in reply_lower:
                self.context.mark_complete(session_id, "SAWS")
            elif any(k.startswith("saws_") for k in self.context.get_collected_fields(session_id)):
                self.context.advance_checklist(session_id, "SAWS")

            if "city of san antonio" in reply_lower and "complete" in reply_lower:
                self.context.mark_complete(session_id, "CITY_SA")
            elif any(k.startswith("city_") for k in self.context.get_collected_fields(session_id)):
                self.context.advance_checklist(session_id, "CITY_SA")

            self.context.add_turn(session_id, message, reply)

            return AgentResponse(
                session_id=session_id,
                reply=reply,
                intent="SIMULATE",
                sources=[],
                checklist=self.context.get_checklist(session_id),
            )

        # ── NORMAL Q&A MODE ────────────────────────────────────────────
        intent = classify_intent(message, self.llm)
        logger.info(f"[{session_id}] Intent: {intent}")

        providers, explicit_match = _detect_providers(message)
        logger.info(f"[{session_id}] Providers: {providers} (explicit={explicit_match})")

        chunks: list[RetrievedChunk] = []
        if intent != Intent.STATUS:
            provider_filter = providers[0] if len(providers) == 1 else None
            raw_chunks = self.retriever.query(message, provider=provider_filter, top_k=TOP_K)
            chunks = [c for c in raw_chunks if c.score <= SCORE_THRESHOLD]
            logger.info(
                f"[{session_id}] {len(raw_chunks)} retrieved, "
                f"{len(chunks)} passed threshold (≤{SCORE_THRESHOLD})"
            )

        history   = self.context.get_history(session_id)
        checklist = self.context.get_checklist(session_id)

        if intent == Intent.STATUS:
            messages = build_status_prompt(message, checklist, history)
        elif intent == Intent.FORM_HELP:
            messages = build_form_help_prompt(message, chunks, history)
        else:
            messages = build_question_prompt(message, chunks, history)

        try:
            reply = self.llm.chat(messages)
        except LLMUnavailableError as e:
            logger.error(f"LLM unavailable: {e}")
            return AgentResponse(
                session_id=session_id,
                reply=(
                    "I'm having trouble reaching the language model right now. "
                    "Please make sure you're on the UTSA network or VPN and try again."
                ),
                intent=intent,
                checklist=checklist,
                error="llm_unavailable",
            )

        if explicit_match:
            for provider in providers:
                self.context.advance_checklist(session_id, provider)

        self.context.add_turn(session_id, message, reply)

        sources = [
            SourceDoc(url=c.url, provider=c.provider, chunk_preview=c.text[:150])
            for c in chunks
        ]

        return AgentResponse(
            session_id=session_id,
            reply=reply,
            intent=intent,
            sources=sources,
            checklist=self.context.get_checklist(session_id),
        )

    def reset(self, session_id: str) -> dict:
        self.context.reset(session_id)
        return {"session_id": session_id, "reset": True}

    def status(self, session_id: str) -> dict:
        return {
            "session_id": session_id,
            "checklist":  self.context.get_checklist(session_id),
            "turn_count": self.context.get_turn_count(session_id),
        }

    # ------------------------------------------------------------------
    # Field extraction from LLM reply + user message
    # ------------------------------------------------------------------

    def _extract_fields_from_reply(self, session_id: str, reply: str, user_message: str):
        """
        Extract confirmed field values from the LLM reply using regex patterns.
        Also uses the user_message to infer simple yes/no answers.
        Stores results in context.collected_fields.
        """
        reply_lower   = reply.lower()
        message_lower = user_message.lower().strip()

        for pattern, field_key in FIELD_CONFIRMATION_PATTERNS:
            # Skip if already collected
            if field_key in self.context.get_collected_fields(session_id):
                continue

            match = re.search(pattern, reply_lower)
            if match:
                # Use the captured group if present, else use the user message as the value
                if match.lastindex and match.group(match.lastindex):
                    value = match.group(match.lastindex).strip().title()
                else:
                    value = user_message.strip()
                self.context.set_field(session_id, field_key, value)
                logger.debug(f"[{session_id}] Extracted field {field_key} = {value}")


def _detect_providers(message: str) -> tuple[list[str], bool]:
    message_lower = message.lower()
    detected = [
        p for p, keywords in PROVIDER_KEYWORDS.items()
        if any(kw in message_lower for kw in keywords)
    ]
    if detected:
        return detected, True
    return list(PROVIDER_KEYWORDS.keys()), False
