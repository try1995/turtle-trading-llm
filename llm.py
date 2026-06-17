"""
Backward-compatible LLM module.
Re-exports a multi-key OpenAI client for code that hasn't been migrated yet,
and provides the new LangChain-based factory.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Multi-key support ──────────────────────────────────────────────
# Parse all API keys (separated by ``|``).  The legacy ``client`` object
# below uses the FIRST key; caller code should use the helper functions
# when a key needs to be rotated.
ALL_API_KEYS = [
    k.strip()
    for k in os.environ.get("api_key", "").split("|")
    if k.strip()
]
NUM_KEYS = len(ALL_API_KEYS)

# Track which key index is currently active for the legacy client
_current_key_index = 0


def _get_legacy_api_key(index: int) -> str:
    """Return the API key at *index* (wraps around)."""
    return ALL_API_KEYS[index % NUM_KEYS] if ALL_API_KEYS else ""


def rotate_legacy_key() -> str:
    """
    Advance the legacy client to the next API key.

    Returns the new active API key.
    """
    global _current_key_index
    _current_key_index = (_current_key_index + 1) % NUM_KEYS
    new_key = _get_legacy_api_key(_current_key_index)
    client.api_key = new_key
    # Recreate the underlying HTTPX client so the new key takes effect
    if hasattr(client, '_client'):
        client._client.close()
        client._client = None
        client._client = client._make_client()
    return new_key


# Legacy OpenAI client — uses the FIRST key initially
client = OpenAI(
    base_url=os.environ.get("base_url"),
    api_key=_get_legacy_api_key(0),
)

# New LangChain-based factory functions
from llm_factory import create_chat_model, create_tool_model, create_vl_model  # noqa: E402, F401
