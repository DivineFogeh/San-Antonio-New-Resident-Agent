# Model Documentation

## LLM — UTSA Llama Endpoint

| Property | Value |
|---|---|
| Model ID | `llama-3.3-70b-instruct-awq` |
| Provider | UTSA GPUStack (hosted endpoint) |
| Base URL | `http://10.246.100.230/v1` (UTSA network/VPN required) |
| API Format | OpenAI-compatible `/v1/chat/completions` |
| License | Meta Llama 3 Community License |
| Temperature | 0.2 |
| Max tokens | 512 |
| Access | Requires UTSA API key (env var: `UTSA_LLM_API_KEY`) |

### Usage

The LLM is called via `crawler/sa_resident_agent/llm/utsa_client.py`. It handles retries (3 attempts, exponential backoff) and raises `LLMUnavailableError` on failure.

### Limitations

- Only accessible on UTSA campus WiFi or VPN
- Rate limited by UTSA infrastructure
- Context window: 128K tokens (Llama 3.3)

---

## Embedding Model — all-MiniLM-L6-v2

| Property | Value |
|---|---|
| Model ID | `sentence-transformers/all-MiniLM-L6-v2` |
| Source | HuggingFace Hub |
| Version | sentence-transformers 2.7.0 |
| License | Apache 2.0 |
| Dimensions | 384 |
| Runtime | Local CPU (no external API) |
| Download | Automatic on first run (~90MB) |

### Usage

Used by `crawler/sa_resident_agent/knowledge/embedder.py` to encode document chunks and user queries for semantic search in ChromaDB.

### Limitations

- CPU-only inference (no GPU required)
- Inference time: ~50ms per chunk on modern CPU
- English-optimized (primary language of SA utility websites)
