"""
Centralized LLM factory using LangChain ChatOpenAI.
Replaces the raw OpenAI client in llm.py with per-agent model configuration.
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Global default settings from environment
DEFAULT_BASE_URL = os.environ.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_API_KEY = os.environ.get("api_key", "")
DEFAULT_MODEL = os.environ.get("model", "qwen-plus-latest")
DEFAULT_TEMPERATURE = 0.1


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

    return ChatOpenAI(
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        model=model,
        temperature=DEFAULT_TEMPERATURE,
        streaming=streaming,
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

    return ChatOpenAI(
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        model=model,
        temperature=DEFAULT_TEMPERATURE,
        streaming=False,  # Tool calls need complete response
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

    return ChatOpenAI(
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        model=model,
        temperature=DEFAULT_TEMPERATURE,
        streaming=True,
    )
