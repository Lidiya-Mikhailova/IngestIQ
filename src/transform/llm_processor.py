from __future__ import annotations

from typing import Any

from openai import APIError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.config.settings import app_settings as settings


class LLMProcessor:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 150,
        temperature: float = 0.3,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to .env file.")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_summary(self, text: str) -> str | None:
        if not text or not text.strip():
            return None

        try:
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": (
                        "You are a data analyst. Generate a brief, informative "
                        "summary (2-3 sentences max) of the provided data. "
                        "Focus on key insights and notable patterns."
                    ),
                },
                {
                    "role": "user",
                    "content": "Summarize the following data:\n\n" + text[:4000],
                },
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except APIError as exc:
            print(f"LLM processing error: {exc}")
            return None

    def batch_generate_summaries(
        self,
        texts: list[str],
        progress_callback: Any = None,
    ) -> list[str | None]:
        results: list[str | None] = []
        total = len(texts)
        for i, text in enumerate(texts):
            summary = self.generate_summary(text)
            results.append(summary)
            if progress_callback:
                progress_callback(i + 1, total)
        return results


def create_llm_processor() -> LLMProcessor:
    return LLMProcessor()
