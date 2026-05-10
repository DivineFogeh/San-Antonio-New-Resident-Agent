# Model Card — SA New Resident Agent

## Intended Use

The SA New Resident Agent is designed to help new residents of San Antonio, Texas set up essential utility and city services. It is intended for:

- New residents unfamiliar with San Antonio utility providers (CPS Energy, SAWS, City of SA)
- Users who need guidance on enrollment steps, required documents, and billing options
- Users who want to complete utility enrollment forms with AI-assisted field guidance

The system operates in two modes:
1. **Q&A mode** (`POST /chat`): Answer questions about rates, documents, and enrollment steps using RAG-grounded responses from indexed utility websites
2. **Simulation mode** (`POST /simulate`): Walk users step by step through the enrollment process, collecting form fields conversationally

**Primary users:** New San Antonio residents, university students, and anyone relocating to San Antonio.

---

## Limitations

- **Geographic scope:** The system only covers San Antonio, Texas utility providers. It cannot answer questions about utility providers in other cities or states.
- **Knowledge freshness:** The ChromaDB index is built by crawling utility websites at a point in time. Rate information, policies, and enrollment requirements may change. Users should verify critical details directly with providers.
- **LLM access:** The UTSA Llama endpoint is only accessible on UTSA campus WiFi or VPN. The system will not function without this connection.
- **Language:** The system is optimized for English. Responses in other languages are not guaranteed.
- **Form submission:** The system simulates enrollment and guides users through forms but does not directly submit applications to CPS Energy, SAWS, or the City of SA. Users must complete final submission on the official provider websites.
- **Context window:** Long conversations may exceed the LLM context window (128K tokens for Llama 3.3). The system retains the last 20 turns.

---

## Risks

- **Outdated information:** If utility provider websites change rates or policies after the index was built, the agent may return outdated information. Mitigation: clearly cite sources and direct users to official websites.
- **Hallucination:** Despite RAG grounding, the LLM may occasionally generate inaccurate details. Mitigation: the system prompt explicitly instructs the model not to fabricate rates, deadlines, or document requirements. The prompt instructs the model to say "I don't have that information" when context is insufficient.
- **API key exposure:** The UTSA LLM API key must not be committed to the repository. Mitigation: `.env` is in `.gitignore`; `.env.example` contains only placeholders.
- **Privacy:** Users enter personal information (name, address, partial SSN) into the form engine. Mitigation: SSN is redacted before saving to JSON. No form data is transmitted to external services in the current implementation.
- **Dependency on UTSA infrastructure:** The system is unavailable if the UTSA LLM endpoint is down. Mitigation: the `utsa_client.py` wrapper implements retry with exponential backoff and raises a clear error.

---

## Out of Scope

The following use cases are explicitly out of scope:

- **Other cities or utilities:** The system does not cover utility providers outside San Antonio.
- **Legal or financial advice:** The system provides factual utility information only. It is not a substitute for legal or financial counsel.
- **Actual form submission:** The system does not submit applications on behalf of users to CPS Energy, SAWS, or the City of SA.
- **Emergency services:** The system is not designed for emergency situations. For gas leaks, power outages, or water emergencies, users should call the provider directly (CPS Energy: 210-353-2222, SAWS: 210-704-7297, City: 311).
- **Non-residential accounts:** The system is designed for residential enrollment only. Commercial, industrial, or contractor accounts are not covered.
- **Medical baseline or special assistance programs:** While the system mentions SAWS Cares, it does not process applications for income-qualified assistance programs.
