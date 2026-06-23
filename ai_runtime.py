from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

try:
    import streamlit as st
except Exception:  # pragma: no cover - allows pure Python imports in tests
    st = None  # type: ignore[assignment]


CONFIG_KEYS = ("AI_NATIVE_LLM_API_KEY", "AI_NATIVE_LLM_ENDPOINT", "AI_NATIVE_LLM_MODEL")


def _read_config_value(name: str) -> str:
    if st is not None:
        try:
            value = st.secrets.get(name, "")
            if value:
                return str(value).strip()
        except Exception:
            pass
    return os.getenv(name, "").strip()


def ai_config() -> dict[str, str]:
    return {name: _read_config_value(name) for name in CONFIG_KEYS}


def ai_available() -> bool:
    return all(ai_config().values())


def ai_mode_label() -> str:
    if ai_available():
        return "AI增强模式：已接入大模型"
    return "本地规则稳定模式：未配置API，使用规则引擎模拟AI"


def _extract_text(result: dict[str, Any]) -> str:
    choices = result.get("choices") or []
    if choices:
        first = choices[0] or {}
        message = first.get("message") or {}
        content = message.get("content") or first.get("text") or ""
        if isinstance(content, str):
            return content.strip()
    content = result.get("content", "")
    return content.strip() if isinstance(content, str) else ""


def optional_ai_text(purpose: str, prompt: str, fallback: str, temperature: float = 0.3) -> str:
    config = ai_config()
    if not all(config.values()):
        return fallback
    system_prompt = (
        "你是AI Native新人培养辅助助手。你只负责辅助分析、内容草案、建议整理和解释。"
        "不要替代本人、导师或HR作最终评价，不要决定晋级、绩效、录用或人才结论。"
        "请使用简洁中文输出。"
    )
    payload = json.dumps(
        {
            "model": config["AI_NATIVE_LLM_MODEL"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"任务：{purpose}\n\n{prompt}"},
            ],
            "temperature": temperature,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        config["AI_NATIVE_LLM_ENDPOINT"],
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {config['AI_NATIVE_LLM_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
        return _extract_text(result) or fallback
    except Exception:
        return fallback


def _parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def optional_ai_json(purpose: str, prompt: str, fallback: dict[str, Any], temperature: float = 0.2) -> dict[str, Any]:
    json_prompt = (
        f"{prompt}\n\n请只输出JSON对象，不要输出Markdown。若信息不足，请用中文短句说明，但仍保持JSON对象结构。"
    )
    text = optional_ai_text(purpose, json_prompt, json.dumps(fallback, ensure_ascii=False), temperature)
    parsed = _parse_json_object(text)
    return parsed if parsed is not None else fallback
