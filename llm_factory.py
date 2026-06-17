"""
Centralized LLM factory using LangChain ChatOpenAI.
Replaces the raw OpenAI client in llm.py with per-agent model configuration.

Supports multiple API keys separated by ``|`` in the ``api_key`` environment
variable.  When a quota / auth error is detected at the call site, the
caller can advance to the next key and retry.
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Global default settings from environment
DEFAULT_BASE_URL = os.environ.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_API_KEY = os.environ.get("api_key", "")
DEFAULT_MODEL = os.environ.get("model", "qwen-plus-latest")
DEFAULT_TEMPERATURE = 0.1

# ── Multi-key support ──────────────────────────────────────────────
# API keys are separated by ``|`` in the env var.  Each key is tried
# in order; on quota/auth failure the caller rotates to the next key.
ALL_API_KEYS = [k.strip() for k in DEFAULT_API_KEY.split("|") if k.strip()]
if not ALL_API_KEYS:
    ALL_API_KEYS = [DEFAULT_API_KEY]


def is_quota_error(e: Exception) -> bool:
    """Return ``True`` if *e* is a quota / auth error that should trigger key rotation."""
    error_msg = str(e).lower()
    return any(phrase in error_msg for phrase in [
        "allocationquota",          # AllocationQuota.FreeTierOnly
        "quota",
        "free tier",
        "exhausted",
        "insufficient_quota",
        "rate limit",
        "insufficient balance",     # 余额不足
    ]) or "403" in error_msg[:200]  # 403 status code near the start


def _create_chat_model_with_key(
    key_index: int,
    model: str,
    streaming: bool,
    temperature: float = DEFAULT_TEMPERATURE,
) -> ChatOpenAI:
    """Create a ``ChatOpenAI`` using the *key_index*-th API key."""
    return ChatOpenAI(
        base_url=DEFAULT_BASE_URL,
        api_key=ALL_API_KEYS[key_index],
        model=model,
        temperature=temperature,
        streaming=streaming,
    )


def create_chat_model(agent_name: str = "", streaming: bool = True) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance configured for a specific agent.

    Model selection priority:
    1. {agent_name}Model environment variable (e.g., dataAgentModel, vlAgentModel)
    2. Global 'model' environment variable
    3. Default "qwen-plus-latest"

    Args:
        agent_name: The agent name (e.g., "dataAgent", "vlAgent").
                    Empty string for default model.
        streaming: Whether to enable streaming by default.

    Returns:
        Configured ChatOpenAI instance.
    """
    model = DEFAULT_MODEL
    if agent_name:
        model = os.environ.get(agent_name + "Model", model)

    return _create_chat_model_with_key(
        key_index=0, model=model, streaming=streaming,
    )


def create_tool_model(agent_name: str = "") -> ChatOpenAI:
    """
    Create a ChatOpenAI instance configured for tool calling.
    Uses toolCallModel env var if set, otherwise falls back to the agent's model.

    Args:
        agent_name: The agent name for fallback model resolution.

    Returns:
        ChatOpenAI instance configured for tool calling (non-streaming).
    """
    model = os.environ.get("toolCallModel")
    if not model:
        model = DEFAULT_MODEL
        if agent_name:
            model = os.environ.get(agent_name + "Model", model)

    return _create_chat_model_with_key(
        key_index=0, model=model, streaming=False,
    )


def create_vl_model(agent_name: str = "vlAgent") -> ChatOpenAI:
    """
    Create a ChatOpenAI instance configured for vision-language tasks.
    Defaults to qwen-vl-plus for image analysis.

    Args:
        agent_name: The agent name for model resolution.

    Returns:
        ChatOpenAI instance configured for VL tasks.
    """
    model = os.environ.get(agent_name + "Model", "qwen-vl-plus")

    return _create_chat_model_with_key(
        key_index=0, model=model, streaming=True,
    )
