# SA Resident Agent — System Specification

**Version:** 1.0  
**Project:** CS 6263 NLP and Agentic AI — Final Project  
**Team scope:** Web Crawling / Knowledge Base / AI Agent Layer  
**Package:** `sa_resident_agent`

---

## 1. Purpose

The SA Resident Agent is a conversational AI assistant that guides new San Antonio residents through utility enrollment with CPS Energy, SAWS (San Antonio Water System), and the City of San Antonio. The system crawls and indexes official service-provider websites into a local vector knowledge base, then exposes a LangChain-powered RAG agent over a FastAPI HTTP interface. Users can ask natural-language questions about rates, required documents, and enrollment steps; the agent retrieves grounded answers from the indexed content, tracks per-session progress, and returns structured responses that the form engine and frontend can act on.

---

## 2. Component Inventory

| Component | Description | Module Path |
|---|---|---|
| CPS Energy Crawler | Crawls and parses CPS Energy service pages | `sa_resident_agent/crawlers/cps_crawler.py` |
| SAWS Crawler | Crawls and parses SAWS service pages | `sa_resident_agent/crawlers/saws_crawler.py` |
| City of SA Crawler | Crawls and parses City of San Antonio permit and registration pages | `sa_resident_agent/crawlers/city_crawler.py` |
| Base Crawler | Shared Playwright + BeautifulSoup logic, retry, rate-limit | `sa_resident_agent/crawlers/base_crawler.py` |
| Document Chunker | Splits raw HTML text into overlapping chunks with metadata | `sa_resident_agent/knowledge/chunker.py` |
| Embedder | Encodes chunks using sentence-transformers `all-MiniLM-L6-v2` | `sa_resident_agent/knowledge/embedder.py` |
| ChromaDB Store | Persists and queries the vector index | `sa_resident_agent/knowledge/vector_store.py` |
| Index Builder | Orchestrates crawl → chunk → embed → store pipeline | `sa_resident_agent/knowledge/index_builder.py` |
| Retriever | Wraps ChromaDB for top-k semantic search | `sa_resident_agent/knowledge/retriever.py` |
| Intent Classifier | Classifies user turn as QUESTION, FORM_HELP, or STATUS | `sa_resident_agent/agent/intent.py` |
| Prompt Templates | Jinja2 templates for RAG QA, form guidance, and status | `sa_resident_agent/agent/prompts.py` |
| Context Manager | Maintains per-session conversation history and checklist state | `sa_resident_agent/agent/context.py` |
| LangChain Agent | Orchestrates retrieval, intent routing, and LLM call | `sa_resident_agent/agent/agent.py` |
| Validator | Validates extracted slot values (address, email, SSN format) | `sa_resident_agent/agent/validator.py` |
| Agent API | FastAPI app exposing `/chat`, `/status`, `/reset` | `sa_resident_agent/api/routes.py` |
| UTSA LLM Client | Thin wrapper around the UTSA Llama HTTP endpoint | `sa_resident_agent/llm/utsa_client.py` |

---

## 3. Data Flow

```
User Message (HTTP POST /chat)
        │
        ▼
    Intent Classifier
        │
   ┌────┴────────────┐
   │                 │
QUESTION         FORM_HELP / STATUS
   │                 │
   ▼                 ▼
Retriever        Context Manager
(ChromaDB)       (session state)
   │                 │
   └────────┬────────┘
            │
            ▼
     Prompt Templates
            │
            ▼
     UTSA Llama Endpoint
            │
            ▼
     Validator (slot extraction)
            │
            ▼
  AgentResponse (JSON) → HTTP Response
```

**Index Build Flow (offline / `make reproduce`):**

```
Playwright browser
    │
    ▼
Base Crawler → CPS / SAWS / City Crawlers
    │
    ▼
Raw HTML + metadata (url, provider, scraped_at)
    │
    ▼
Document Chunker (chunk_size=512, overlap=64 tokens)
    │
    ▼
Embedder (all-MiniLM-L6-v2, dim=384)
    │
    ▼
ChromaDB (persisted at data/chroma/)
```

---

## 4. Public Interfaces

### 4.1 POST `/chat`

Sends a user message and receives an agent response.

**Request**
```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response**
```json
{
  "session_id": "string",
  "reply": "string",
  "intent": "QUESTION | FORM_HELP | STATUS",
  "sources": [
    {
      "url": "string",
      "provider": "CPS_ENERGY | SAWS | CITY_SA",
      "chunk_preview": "string"
    }
  ],
  "checklist": {
    "cps_energy": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "saws": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "city_sa": "NOT_STARTED | IN_PROGRESS | COMPLETE"
  },
  "validated_slots": {
    "field_name": "value"
  }
}
```

**Errors**

| Status | Condition |
|---|---|
| 422 | Missing or malformed `session_id` or `message` |
| 503 | UTSA LLM endpoint unreachable |

---

### 4.2 GET `/status/{session_id}`

Returns the current checklist state for a session without sending a message.

**Response**
```json
{
  "session_id": "string",
  "checklist": {
    "cps_energy": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "saws": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "city_sa": "NOT_STARTED | IN_PROGRESS | COMPLETE"
  },
  "turn_count": "integer"
}
```

---

### 4.3 POST `/reset`

Clears session history and resets checklist to `NOT_STARTED`.

**Request**
```json
{
  "session_id": "string"
}
```

**Response**
```json
{
  "session_id": "string",
  "reset": true
}
```

---

### 4.4 GET `/health`

Liveness probe used by Docker health check.

**Response**
```json
{
  "status": "ok",
  "chroma_docs": "integer",
  "llm_reachable": "boolean"
}
```

---

### 4.5 IndexBuilder Python Interface

Used by `make reproduce` and `make download-data`.

```python
class IndexBuilder:
    def build(self, providers: list[str] = ["CPS_ENERGY", "SAWS", "CITY_SA"]) -> IndexBuildResult:
        """Crawl, chunk, embed, and persist all providers. Returns doc counts and errors."""

    def rebuild(self, provider: str) -> IndexBuildResult:
        """Drop and rebuild the index for a single provider."""
```

---

### 4.6 Retriever Python Interface

Used internally by the agent; also callable from tests.

```python
class Retriever:
    def query(self, text: str, provider: str | None = None, top_k: int = 5) -> list[RetrievedChunk]:
        """Semantic search over ChromaDB. Optional provider filter."""
```

```python
@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    url: str
    provider: str
    score: float
```

---

### 4.7 Validator Python Interface

Used by the agent and callable by the form engine.

```python
class Validator:
    def validate(self, field: str, value: str) -> ValidationResult:
        """Validate a single form field value. Returns valid flag and error message."""
```

```python
@dataclass
class ValidationResult:
    field: str
    value: str
    valid: bool
    error: str | None
```

---

## 5. Model and Prompt Selection

### 5.1 LLM

| Property | Value |
|---|---|
| Model | `meta-llama/Llama-3.1-8B-Instruct` (UTSA hosted endpoint) |
| Temperature | `0.2` |
| Max tokens | `512` |
| Endpoint env var | `UTSA_LLM_BASE_URL` |

The UTSA endpoint is accessed via `POST /v1/chat/completions` with an OpenAI-compatible payload. The `utsa_client.py` wrapper handles retries (3 attempts, exponential backoff) and raises `LLMUnavailableError` on failure.

### 5.2 Embedding Model

| Property | Value |
|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Runtime | Local CPU (no external API) |
| Loaded via | `sentence_transformers.SentenceTransformer` |

### 5.3 Prompt Templates

**RAG QA Prompt** (`prompts.py :: RAG_QA_TEMPLATE`)

```
You are a helpful assistant for new San Antonio residents setting up utilities.
Answer the user's question using only the context below. If the answer is not in
the context, say "I don't have that information — please visit {provider_url}."
Do not make up rates, deadlines, or document requirements.

Context:
{retrieved_chunks}

Conversation history:
{history}

User: {user_message}
Assistant:
```

**Form Guidance Prompt** (`prompts.py :: FORM_HELP_TEMPLATE`)

```
You are guiding a new San Antonio resident through a utility signup form for {provider}.
The user needs help with the field: {field_name}.
Based on the following policy context, explain what is required and give an example.

Context:
{retrieved_chunks}

User: {user_message}
Assistant:
```

**Intent Classification Prompt** (`prompts.py :: INTENT_TEMPLATE`)

```
Classify the following user message into exactly one of: QUESTION, FORM_HELP, STATUS.
- QUESTION: user is asking about rates, policies, documents, or requirements
- FORM_HELP: user is filling out a form or needs field-level guidance
- STATUS: user is asking about their setup progress or checklist

Respond with only the label.

Message: {user_message}
```

### 5.4 Chunking Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Chunk size | 512 tokens | Fits LLM context with room for history |
| Overlap | 64 tokens | Preserves sentence boundaries across chunks |
| Splitter | `RecursiveCharacterTextSplitter` (LangChain) | Respects paragraph structure |
| Metadata fields | `url`, `provider`, `scraped_at`, `chunk_index` | Required for source citation |