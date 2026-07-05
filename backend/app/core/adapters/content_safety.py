"""Thin async wrapper around Azure AI Content Safety (REST via aiohttp).

Two checks on user input:
- **Prompt Shields** (`text:shieldPrompt`) — detects jailbreak / prompt-injection.
- **Text moderation** (`text:analyze`) — hate / self-harm / sexual / violence severities.

Fails **open** (returns "not unsafe") on service errors: a Content Safety outage
shouldn't take down chat, and the other guardrails still apply — Azure OpenAI's
own default content filter on the completion, the grounded system prompt, and RAG
containment. See ``rag_service`` for where these are called.
"""

import logging

import aiohttp

from core.config import settings

logger = logging.getLogger(__name__)

API_VERSION = "2024-09-01"
HARM_CATEGORIES = ["Hate", "SelfHarm", "Sexual", "Violence"]


class ContentSafetyClient:
    def __init__(self) -> None:
        self._endpoint = settings.azure_content_safety_endpoint.rstrip("/")
        self._threshold = settings.content_safety_threshold
        self._session = aiohttp.ClientSession(
            headers={
                "Ocp-Apim-Subscription-Key": settings.azure_content_safety_key,
                "Content-Type": "application/json",
            }
        )

    async def close(self) -> None:
        await self._session.close()

    async def detect_prompt_attack(self, text: str) -> bool:
        """Prompt Shields: True if a jailbreak / prompt-injection attempt is detected."""
        url = f"{self._endpoint}/contentsafety/text:shieldPrompt?api-version={API_VERSION}"
        try:
            async with self._session.post(
                url, json={"userPrompt": text, "documents": []}
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception:
            logger.exception("Prompt Shields request failed; failing open")
            return False
        return bool((data.get("userPromptAnalysis") or {}).get("attackDetected"))

    async def is_text_harmful(self, text: str) -> bool:
        """Text moderation: True if any category meets/exceeds the severity threshold."""
        url = f"{self._endpoint}/contentsafety/text:analyze?api-version={API_VERSION}"
        try:
            async with self._session.post(
                url, json={"text": text, "categories": HARM_CATEGORIES}
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception:
            logger.exception("Content Safety analyze failed; failing open")
            return False
        for item in data.get("categoriesAnalysis", []):
            severity = item.get("severity") or 0
            if severity >= self._threshold:
                logger.warning(
                    "Harmful content: %s severity %s", item.get("category"), severity
                )
                return True
        return False
