"""
sa_resident_agent/agent/context.py

Per-session state: conversation history + utility setup checklist + collected fields.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

PROVIDERS = ["CPS_ENERGY", "SAWS", "CITY_SA"]
MAX_HISTORY_TURNS = 6


class ChecklistStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE    = "COMPLETE"


@dataclass
class SessionState:
    session_id: str
    history: list[dict] = field(default_factory=list)
    checklist: dict[str, str] = field(default_factory=lambda: {
        p: ChecklistStatus.NOT_STARTED for p in PROVIDERS
    })
    turn_count: int = 0
    # Tracks fields collected during simulate mode — never reset between turns
    collected_fields: dict[str, str] = field(default_factory=dict)
    current_provider: str = "CPS_ENERGY"  # tracks which provider we're on


class ContextManager:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> SessionState:
        self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def add_turn(self, session_id: str, user_message: str, assistant_reply: str):
        state = self.get_or_create(session_id)
        state.history.append({"role": "user",      "content": user_message})
        state.history.append({"role": "assistant",  "content": assistant_reply})
        state.turn_count += 1
        max_messages = MAX_HISTORY_TURNS * 2
        if len(state.history) > max_messages:
            state.history = state.history[-max_messages:]

    def get_history(self, session_id: str) -> list[dict]:
        return list(self.get_or_create(session_id).history)

    def advance_checklist(self, session_id: str, provider: str):
        state = self.get_or_create(session_id)
        current = state.checklist.get(provider, ChecklistStatus.NOT_STARTED)
        if current == ChecklistStatus.NOT_STARTED:
            state.checklist[provider] = ChecklistStatus.IN_PROGRESS

    def mark_complete(self, session_id: str, provider: str):
        state = self.get_or_create(session_id)
        state.checklist[provider] = ChecklistStatus.COMPLETE

    def get_checklist(self, session_id: str) -> dict[str, str]:
        return dict(self.get_or_create(session_id).checklist)

    def get_turn_count(self, session_id: str) -> int:
        return self.get_or_create(session_id).turn_count

    # ------------------------------------------------------------------
    # Simulate mode field tracking
    # ------------------------------------------------------------------

    def set_field(self, session_id: str, field_name: str, value: str):
        """Store a collected field value."""
        state = self.get_or_create(session_id)
        state.collected_fields[field_name] = value

    def get_collected_fields(self, session_id: str) -> dict[str, str]:
        return dict(self.get_or_create(session_id).collected_fields)

    def get_fields_summary(self, session_id: str) -> str:
        """Return a formatted string of all collected fields for injection into prompt."""
        fields = self.get_or_create(session_id).collected_fields
        if not fields:
            return "No fields collected yet."
        return "\n".join(f"  {k}: {v}" for k, v in fields.items())
