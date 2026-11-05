from collections.abc import Iterator

from openai import OpenAI

from app.config import settings


class GroqService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_api_url,
        )
        self.model = settings.groq_ai_model

    def _build_input(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_prompt: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            *messages,
            {"role": "user", "content": user_prompt},
        ]

    def generate_response(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_input(system_prompt, messages, user_prompt),
            tools=[{"type": "browser_search"}],
        )

        return response.choices[0].message.content

    def generate_response_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_prompt: str,
    ) -> Iterator[str]:

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_input(system_prompt, messages, user_prompt),
            tools=[{"type": "browser_search"}],
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content
            if content:
                yield content



groq_service = GroqService()
