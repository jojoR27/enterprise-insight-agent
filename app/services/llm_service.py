from functools import lru_cache

from openai import AsyncOpenAI

from app.config import get_settings


class LLMService:
    def __init__(self):
        settings = get_settings()

        if not settings.llm_api_key:
            raise RuntimeError(
                "LLM_API_KEY 未配置"
            )

        if not settings.llm_model:
            raise RuntimeError(
                "LLM_MODEL 未配置"
            )

        self.model = settings.llm_model

        if settings.llm_base_url:
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
        else:
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
            )

    async def answer_with_context(
            self,
            query: str,
            context: str,
    ) -> str:
        response = (
            await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是企业知识库问答助手。\n"
                            "你只能依据提供的知识库资料回答问题。\n"
                            "禁止使用知识库之外的信息补充答案。\n\n"

                            "引用规则：\n"
                            "1. 知识库资料已经带有"
                            "[来源1]、[来源2]等编号。\n"
                            "2. 回答中凡是使用某条资料得出的事实，"
                            "必须在对应内容后标注该来源。\n"
                            "3. 引用格式必须严格使用：[来源1]\n"
                            "4. 可以同时引用多个来源，例如："
                            "[来源1][来源2]\n"
                            "5. 禁止编造不存在的来源编号。\n"
                            "6. 如果资料无法支持答案，"
                            "只回答：根据当前知识库资料无法确定。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"用户问题：\n{query}\n\n"
                            f"知识库资料：\n{context}"
                        ),
                    },
                ],
            )
        )

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            raise RuntimeError(
                "LLM 返回内容为空"
            )

        return content


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()