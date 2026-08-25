# 把Generator+Validator+Executor封装成一个 LangChain Tool


import json

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.text2sql.sql_executor import (
    SQLExecutionError,
    SQLExecutionRejectedError,
    execute_readonly_sql,
)
from app.text2sql.sql_generator import (
    generate_sql,
)
from app.text2sql.sql_validator import (
    validate_sql,
)
from app.observability.trace import AgentTrace


class TextToSQLInput(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description=(
            "需要通过数据库分析回答的销售业务问题。"
            "例如：各渠道销售额占比、"
            "复杂排名、多维度统计、趋势分析等。"
        ),
    )


def create_text2sql_tool(trace: AgentTrace | None = None,):
    @tool(
        "text_to_sql",
        args_schema=TextToSQLInput,
    )

    async def text_to_sql(question: str,) -> str:
        """
        使用安全 Text-to-SQL 分析企业销售表数据。

        当简单的地区、产品、渠道、日期分组统计
        无法满足用户问题时使用。

        工具内部会依次执行：
        SQL Generator
        -> SQL Validator
        -> Read-only SQL Executor
        """
        step = None

        if trace is not None:
            step = trace.start_step(
                name="text_to_sql",
                category="tool",
                metadata={
                    "question_length": len(question),
                },
            )

        try:
            # ==========================================
            # 1. Natural Language -> SQL
            # ==========================================
            generation = await generate_sql(question)

            generated_sql = (generation.sql.strip())

            # ==========================================
            # 2. SQL 安全校验
            # ==========================================

            validation = validate_sql(generated_sql)

            if not validation.is_valid:
                if (
                        trace is not None
                        and step is not None
                ):
                    trace.finish_step(
                        step,
                        success=False,
                        error=(
                            "SQL validation rejected "
                            "generated SQL"
                        ),
                        metadata={
                            "stage": "validation",
                            "validation_error_count": len(
                                validation.errors
                            ),
                            "warning_count": len(
                                validation.warnings
                            ),
                        },
                    )

                result = {
                    "success": False,
                    "stage": "validation",
                    "question": question,
                    "generated_sql": generated_sql,
                    "explanation": (
                        generation.explanation
                    ),
                    "errors": (
                        validation.errors
                    ),
                    "warnings": (
                        validation.warnings
                    ),
                }

                return json.dumps(
                    result,
                    ensure_ascii=False,
                )

            # ==========================================
            # 3. Read-only SQL Executor
            # ==========================================

            try:
                execution = (
                    await execute_readonly_sql(generated_sql)
                )

            except SQLExecutionRejectedError as exc:
                if (
                        trace is not None
                        and step is not None
                ):
                    trace.finish_step(
                        step,
                        success=False,
                        error=str(exc),
                        metadata={
                            "stage": "executor_rejected",
                        },
                    )

                result = {
                    "success": False,
                    "stage": "executor_rejected",
                    "question": question,
                    "generated_sql": generated_sql,
                    "error": str(exc),
                }

                return json.dumps(
                    result,
                    ensure_ascii=False,
                )

            except SQLExecutionError as exc:
                if (
                        trace is not None
                        and step is not None
                ):
                    trace.finish_step(
                        step,
                        success=False,
                        error=str(exc),
                        metadata={
                            "stage": "execution",
                        },
                    )

                result = {
                    "success": False,
                    "stage": "execution",
                    "question": question,
                    "generated_sql": generated_sql,
                    "error": str(exc),
                }

                return json.dumps(
                    result,
                    ensure_ascii=False,
                )

            # ==========================================
            # 4. 返回结构化查询结果
            # ==========================================

            result = {
                "success": True,
                "question": question,
                "generated_sql": (
                    execution.sql
                ),
                "sql_explanation": (
                    generation.explanation
                ),
                "columns": (
                    execution.columns
                ),
                "row_count": (
                    execution.row_count
                ),
                "truncated": (
                    execution.truncated
                ),
                "rows": (
                    execution.rows
                ),
            }

            if (
                    trace is not None
                    and step is not None
            ):
                trace.finish_step(
                    step,
                    metadata={
                        "stage": "completed",
                        "row_count": (
                            execution.row_count
                        ),
                        "truncated": (
                            execution.truncated
                        ),
                    },
                )

            return json.dumps(
                result,
                ensure_ascii=False,
            )

        except Exception as exc:
            if (
                    trace is not None
                    and step is not None
                    and step.finished_at is None
            ):
                trace.finish_step(
                    step,
                    success=False,
                    error=str(exc),
                    metadata={
                        "stage": "unexpected_error",
                    },
                )
            raise

    return text_to_sql