from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .config import Settings
from .models import ChatCompletionRequest


def _message_text(content: str | list[dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    pieces: list[str] = []
    for item in content:
        if item.get("type") in {"text", "input_text"} and isinstance(
            item.get("text"), str
        ):
            pieces.append(item["text"])
    return "\n".join(pieces)


class LocalBackend:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    @property
    def is_echo(self) -> bool:
        return not self.settings.local_backend_url

    async def chat(self, request: ChatCompletionRequest) -> dict[str, Any]:
        if self.settings.local_backend_url:
            response = await self._client.post(
                f"{self.settings.local_backend_url}/v1/chat/completions",
                json=request.model_dump(exclude_none=True),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

        user_text = ""
        for message in reversed(request.messages):
            if message.role == "user":
                user_text = _message_text(message.content)
                break
        text = f"neuron-mesh echo: {user_text or '[empty user message]'}"
        prompt_chars = sum(len(_message_text(message.content)) for message in request.messages)
        prompt_tokens = max(1, prompt_chars // 4)
        completion_tokens = max(1, len(text) // 4)
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "system_fingerprint": "neuron-mesh-echo-v1",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    async def stream_text(self, response: dict[str, Any]) -> AsyncIterator[str]:
        text = response["choices"][0]["message"]["content"]
        response_id = response["id"]
        created = response["created"]
        model = response["model"]
        chunks = [text[index : index + 16] for index in range(0, len(text), 16)] or [""]
        for index, chunk in enumerate(chunks):
            event = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": (
                            {"role": "assistant", "content": chunk}
                            if index == 0
                            else {"content": chunk}
                        ),
                        "finish_reason": None,
                    }
                ],
            }
            import json

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        final = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        import json

        yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    async def close(self) -> None:
        await self._client.aclose()

