# 把用户自然语言 + Schema Registry 交给 DeepSeek，让它生成 PostgreSQL SQL。

# 第二层
# SQL Generator Prompt
# → 要求只生成 SELECT

from functools import lru_cache

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from pydantic import BaseModel, Field

from app.agents.model import (
    get_structured_base_model,
)
from app.text2sql.schema_registry import (
    get_schema_prompt,
)


class SQLGenerationResult(BaseModel):
    sql: str = Field(
        description=(
            "根据用户问题生成的 PostgreSQL "
            "只读查询 SQL。"
        )
    )

    explanation: str = Field(
        description=(
            "简短说明这条 SQL "
            "如何回答用户的问题。"
        )
    )


@lru_cache
def get_sql_generator_model():
    model = get_structured_base_model()

    return model.with_structured_output(
        SQLGenerationResult,
        method="function_calling",
    )


async def generate_sql(question: str,) -> SQLGenerationResult:
    schema_prompt = get_schema_prompt()

    model = get_sql_generator_model()

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent "
                    "中的 PostgreSQL SQL 生成器。\n\n"

                    "你的唯一任务是："
                    "根据用户问题和提供的数据库 Schema，"
                    "生成一条用于回答问题的 PostgreSQL "
                    "查询 SQL。\n\n"

                    "必须遵守以下规则：\n"
                    "1. 只能根据提供的 Schema 生成 SQL。\n"
                    "2. 不得使用 Schema 中不存在的表或字段。\n"
                    "3. 只生成查询用途的 SQL。\n"
                    "4. 禁止生成 INSERT、UPDATE、DELETE、"
                    "DROP、ALTER、TRUNCATE、CREATE 等"
                    "修改数据库的操作。\n"
                    "5. 原则上只生成一条 SQL 语句。\n"
                    "6. 用户没有要求全部明细时，"
                    "应尽量避免返回无限量数据。\n"
                    "7. SQL 使用 PostgreSQL 语法。\n"
                    "8. 销售日期分析使用 sale_date，"
                    "不要误用 created_at。\n"
                    "9. 销售额默认使用 SUM(revenue)。\n"
                    "10. 销量默认使用 SUM(quantity)。\n"
                    "11. 不要在 SQL 中加入 Markdown "
                    "代码块标记。\n\n"

                    "重要："
                    "你目前只负责生成 SQL，"
                    "SQL 后续还会经过安全 Validator。"
                )
            ),
            HumanMessage(
                content=(
                    f"{schema_prompt}\n\n"
                    "============================\n\n"
                    f"用户问题：\n{question}\n\n"
                    "请生成能够回答该问题的 PostgreSQL SQL。"
                )
            ),
        ]
    )

    return response