from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import get_settings


def _create_model(enable_thinking: bool | None = None) -> ChatOpenAI:
    settings = get_settings()

    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY 未配置")

    if not settings.llm_model:
        raise RuntimeError("LLM_MODEL 未配置")

    kwargs = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
    }

    if enable_thinking is not None:
        kwargs["extra_body"] = {"enable_thinking": enable_thinking}

    return ChatOpenAI(**kwargs)


@lru_cache
def get_agent_model() -> ChatOpenAI:
    """
    主 Agent 模型。
    保持 deepseek-v4-flash 默认思考模式。
    """
    return _create_model()

@lru_cache
def get_structured_base_model() -> ChatOpenAI:
    """
    结构化输出专用基础模型。
    关闭思考模式，
    供 Planner、SQL Generator 等
    function calling 场景使用。
    """
    return _create_model(
        enable_thinking=False,
    )