"""
sa_resident_agent/llm/utsa_client.py

Thin HTTP client for the UTSA-hosted Llama endpoint.
OpenAI-compatible /v1/chat/completions API — no API key required.
Only accessible on UTSA network or VPN.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = os.getenv("UTSA_LLM_BASE_URL", "http://10.246.100.230/v1")
DEFAULT_MODEL    = os.getenv("UTSA_LLM_MODEL", "llama-3.3-70b-instruct-awq")

MAX_RETRIES    = 3
TIMEOUT_SECS   = 60.0   # 70B model can be slow under load


class LLMUnavailableError(Exception):
    """Raised when the UTSA LLM endpoint cannot be reached after retries."""


class UTSAClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        self.base_url    = base_url.rstrip("/")
        self.model       = model
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self._client     = httpx.Client(timeout=TIMEOUT_SECS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request. Returns the assistant reply as a string.

        Args:
            messages:    List of {"role": "user"|"assistant"|"system", "content": str}
            temperature: Override instance default.
            max_tokens:  Override instance default.

        Raises:
            LLMUnavailableError: If the endpoint is unreachable after MAX_RETRIES.
        """
        payload = {
            "model":       self.model,
            "messages":    messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens":  max_tokens  if max_tokens  is not None else self.max_tokens,
        }

        url = f"{self.base_url}/chat/completions"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"LLM request attempt {attempt}/{MAX_RETRIES} → {url}")
                #response = self._client.post(url, json=payload)
                headers = {}
                api_key = os.getenv("UTSA_LLM_API_KEY", "")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                response = self._client.post(url, json=payload, headers=headers)
                
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                logger.debug(f"LLM reply ({len(reply)} chars): {reply[:80]}...")
                return reply

            except httpx.HTTPStatusError as e:
                logger.warning(f"LLM HTTP error {e.response.status_code} on attempt {attempt}: {e}")
            except httpx.RequestError as e:
                logger.warning(f"LLM connection error on attempt {attempt}: {e}")
            except (KeyError, IndexError) as e:
                logger.warning(f"Unexpected LLM response format on attempt {attempt}: {e}")

            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

        raise LLMUnavailableError(
            f"UTSA LLM endpoint unreachable after {MAX_RETRIES} attempts. "
            f"Are you on the UTSA network or VPN?"
        )

    #def is_reachable(self) -> bool:
    #    """Quick liveness check — used by /health endpoint."""
    #    try:
    #        resp = self._client.get(f"{self.base_url}/models", timeout=5.0)
    #        return resp.status_code == 200
    #    except Exception:
     #       return False
    
    def is_reachable(self) -> bool:
            try:
                headers = {}
                api_key = os.getenv("UTSA_LLM_API_KEY", "")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                resp = self._client.get(f"{self.base_url}/models", timeout=5.0, headers=headers)
                return resp.status_code == 200
            
            except Exception:
                return False

    def close(self):
        self._client.close()
