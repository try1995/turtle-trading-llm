"""
Backward-compatible LLM module.
Re-exports the legacy OpenAI client for code that hasn't been migrated yet,
and provides the new LangChain-based factory.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Legacy OpenAI client — maintained for backward compatibility
client = OpenAI(
    base_url=os.environ.get("base_url"),
    api_key=os.environ.get("api_key"),
)

# New LangChain-based factory functions
from llm_factory import create_chat_model, create_tool_model, create_vl_model  # noqa: E402, F401
