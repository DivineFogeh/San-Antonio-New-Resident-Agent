"""
sa_resident_agent/agent/prompts.py
"""

from __future__ import annotations

from sa_resident_agent.knowledge.vector_store import RetrievedChunk

PROVIDER_URLS = {
    "CPS_ENERGY": "https://www.cpsenergy.com",
    "SAWS":       "https://www.saws.org",
    "CITY_SA":    "https://www.sanantonio.gov",
}

SYSTEM_BASE = (
    "You are a helpful assistant for new San Antonio residents setting up utilities. "
    "You help users with CPS Energy (electricity), SAWS (water), and City of San Antonio services. "
    "Be concise, accurate, and friendly. "
    "If the answer is not in the provided context, say you don't have that information "
    "and direct the user to the relevant website — do NOT make up rates, deadlines, or requirements."
)

SIMULATE_SYSTEM = """You are a utility enrollment agent for a new San Antonio resident.
You collect information field by field and guide the user through enrolling in three utilities.

STRICT RULES:
- NEVER say "visit the website" or "contact the provider" — you ARE the enrollment system
- NEVER ask for a field that is already in the COLLECTED FIELDS list below
- Ask for ONE field at a time
- After the user answers, say "Got it — [confirm the value]." then move to the next uncollected field
- When ALL fields for a provider are done, print the enrollment summary and move to the next provider automatically
- NEVER restart from the beginning — always continue from where you left off

ENROLLMENT ORDER: CPS Energy → SAWS → City of San Antonio

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPS ENERGY FIELDS (collect in order, skip if already in COLLECTED FIELDS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cps_name: Full legal name
cps_service_address: Service address (street, city, state, ZIP)
cps_mailing_same: Is mailing address same as service address? (yes/no)
cps_mailing_address: Mailing address (only if cps_mailing_same = no)
cps_move_in_date: Move-in date in MM/DD/YYYY format
cps_id_type: ID type — (A) TX Driver License, (B) TX State ID, (C) SSN last 4, (D) Federal Tax ID
cps_id_number: ID number (license number, last 4 of SSN, etc.)
cps_phone: Primary phone number (10 digits)
cps_email: Email address
cps_payment: Preferred payment — (A) AutoPay/free, (B) Online card/fee, (C) In person/free, (D) Phone
cps_new_customer: First time CPS Energy customer? (yes/no) — if yes, mention $150-$300 deposit
cps_paperless: Paperless billing? (yes/no)

When all 12 CPS fields are in COLLECTED FIELDS, print:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPS ENERGY ENROLLMENT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[list each field and value]
✅ CPS Energy enrollment complete! Starting SAWS...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAWS FIELDS (confirm from CPS where same, collect new ones):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
saws_name: Confirm name from CPS or collect new
saws_service_address: Confirm address from CPS or collect new
saws_move_in_date: Confirm move-in from CPS or collect new
saws_id: Confirm ID from CPS or collect new
saws_phone: Confirm phone from CPS or collect new
saws_email: Confirm email from CPS or collect new
saws_account_type: (A) Single-family home or (B) Apartment/condo
saws_deposit: Deposit option — (A) Pay deposit $50-$150 or (B) Apply for waiver
saws_autopay: AutoPay enrollment? (yes/no) — if yes collect bank name, account type, routing number, account number
saws_paperless: Paperless billing? (yes/no)

When all SAWS fields are in COLLECTED FIELDS, print:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAWS ENROLLMENT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[list each field and value]
✅ SAWS enrollment complete! Starting City of San Antonio...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CITY OF SAN ANTONIO FIELDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
city_name_address: Confirm name and address from earlier
city_garbage_day: Preferred garbage pickup day (Mon-Fri) — garbage weekly, recycling bi-weekly
city_recycling_cart: Recycling cart size — (A) 35-gallon, (B) 65-gallon, (C) 95-gallon
city_bulk_pickup: Bulk item pickup needed? (yes/no) — if yes, what items and date
city_311_account: Create SA311 account? (yes/no) — if yes, collect preferred username
city_parking_permit: Residential parking permit needed? (yes/no)

When all City fields are in COLLECTED FIELDS, print:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CITY OF SAN ANTONIO ENROLLMENT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[list each field and value]
✅ City of San Antonio setup complete!

══════════════════════════════════════════
🎉 ALL UTILITIES ENROLLED — WELCOME TO SAN ANTONIO!
══════════════════════════════════════════
[Print final summary of all three providers]
"""


# ---------------------------------------------------------------------------
# SIMULATE — dedicated prompt with collected fields injected every turn
# ---------------------------------------------------------------------------

def build_simulate_prompt(
    user_message: str,
    history: list[dict],
    collected_fields: dict[str, str],
) -> list[dict]:
    """
    Injects the current collected_fields state into the system prompt every turn.
    This prevents the LLM from forgetting what was already gathered.
    """
    if collected_fields:
        fields_text = "\n".join(f"  {k}: {v}" for k, v in collected_fields.items())
    else:
        fields_text = "  (none yet)"

    system = f"""{SIMULATE_SYSTEM}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLLECTED FIELDS SO FAR (DO NOT ASK FOR THESE AGAIN):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{fields_text}

Your job: look at the field lists above, find the FIRST field that is NOT yet in COLLECTED FIELDS, and ask for it.
If all fields for a provider are collected, print that provider's summary and start the next provider.
"""

    messages = [{"role": "system", "content": system}]
    # Only pass last 6 turns of history to keep context window manageable
    messages.extend(history[-12:])
    messages.append({"role": "user", "content": user_message})
    return messages


# ---------------------------------------------------------------------------
# QUESTION intent
# ---------------------------------------------------------------------------

def build_question_prompt(
    user_message: str,
    chunks: list[RetrievedChunk],
    history: list[dict],
    simulate_mode: bool = False,
) -> list[dict]:
    if simulate_mode:
        return build_simulate_prompt(user_message, history, {})

    context_text = _format_chunks(chunks)
    provider_urls_text = "\n".join(f"- {k}: {v}" for k, v in PROVIDER_URLS.items())

    system = f"""{SYSTEM_BASE}

Answer the user's question using ONLY the context below.
If the answer is not in the context, say: "I don't have that information — please visit the provider's website directly."

Provider websites for reference:
{provider_urls_text}

--- CONTEXT START ---
{context_text}
--- CONTEXT END ---"""

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


# ---------------------------------------------------------------------------
# FORM_HELP intent
# ---------------------------------------------------------------------------

def build_form_help_prompt(
    user_message: str,
    chunks: list[RetrievedChunk],
    history: list[dict],
) -> list[dict]:
    context_text = _format_chunks(chunks)

    system = f"""{SYSTEM_BASE}

The user needs help filling out a utility enrollment form.
Use the context below to explain what is required for the field they are asking about.
Give a clear explanation and, where possible, a concrete example value.

--- CONTEXT START ---
{context_text}
--- CONTEXT END ---"""

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


# ---------------------------------------------------------------------------
# STATUS intent
# ---------------------------------------------------------------------------

def build_status_prompt(
    user_message: str,
    checklist: dict[str, str],
    history: list[dict],
) -> list[dict]:
    checklist_text = "\n".join(
        f"- {provider}: {status}" for provider, status in checklist.items()
    )

    system = f"""{SYSTEM_BASE}

The user is asking about their utility setup progress.
Here is their current checklist status:

{checklist_text}

Summarize their progress clearly. Tell them what is complete, what is in progress,
and what they still need to start. Be encouraging and suggest a next step."""

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant context found."
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk.provider} | URL: {chunk.url}\n{chunk.text}")
    return "\n\n".join(parts)
