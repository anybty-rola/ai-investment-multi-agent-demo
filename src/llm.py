from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    provider: str = "deepseek"
    temperature: float = 0.2
    max_tokens: int = 1600
    extra_headers: dict[str, str] = field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key.strip())


class DeepSeekClient:
    """Tiny OpenAI-compatible chat client for DeepSeek.

    The API key is passed at runtime and is never persisted by the app.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.config.enabled:
            return ""

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                **self.config.extra_headers,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"DeepSeek API HTTP {exc.code}: {error_body}") from exc
        except Exception as exc:
            raise RuntimeError(f"DeepSeek API 调用失败：{exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"DeepSeek API 返回格式异常：{data}") from exc
