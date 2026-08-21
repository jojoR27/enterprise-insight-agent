# 规定llm返回路由结果的格式

from functools import lru_cache

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import BaseModel, Field

from app.agents.model import get_router_base_model
from app.graph.state import (
    EnterpriseGraphState,
    RouteName,
)


class RouteDecision(BaseModel):
    route: RouteName = Field(
        description=(
            "knowledge：企业制度、员工手册、"
            "年假、报销、考勤、培训等知识库问题；"
            "sql：销售额、销量、地区、产品、渠道、"
            "日期范围、经营统计等结构化数据问题；"
            "chat 表示普通聊天、通用问题或关于当前对话的问题"
        )
    )

    reason: str = Field(
        description="选择该路由的简短原因"
    )


@lru_cache
def get_router_model():
    model = get_router_base_model()

    return model.with_structured_output(
        RouteDecision,
        method="function_calling",
    )


def format_conversation(
    state: EnterpriseGraphState,
    limit: int = 8,
) -> str:
    lines: list[str] = []

    for message in state["messages"][-limit:]:
        if isinstance(message, HumanMessage):
            lines.append(
                f"用户：{message.content}"
            )

        elif (
            isinstance(message, AIMessage)
            and message.content
        ):
            lines.append(
                f"助手：{message.content}"
            )

    return "\n".join(lines)


async def router_node(
    state: EnterpriseGraphState,
) -> dict:
    router_model = get_router_model()

    conversation = format_conversation(
        state
    )

    decision = await router_model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent "
                    "的请求路由器。"
                    "你只负责分类，不负责回答用户问题。\n\n"

                    "路由规则：\n"
                    "knowledge："
                    "公司制度、员工手册、年假、考勤、"
                    "报销、培训、信息安全、内部流程等"
                    "企业内部知识。\n"
                    
                    "sql：\n"
                    "涉及销售额、销量、销售地区、产品、"
                    "销售渠道、销售日期、销售统计、"
                    "经营数据计算的问题。\n"

                    "chat："
                    "普通寒暄、通用聊天，或者询问"
                    "当前聊天历史本身的问题。\n\n"

                    "如果用户当前问题是省略式追问，"
                    "例如“那要提前几天？”，"
                    "必须结合之前对话判断其真实主题。"
                )
            ),
            HumanMessage(
                content=(
                    "最近对话如下：\n\n"
                    f"{conversation}\n\n"
                    "请判断最后一条用户消息"
                    "应该进入哪个路由。"
                )
            ),
        ]
    )

    return {
        "route": decision.route,
        "route_reason": decision.reason,

        # 每轮重新计算，防止沿用上一轮工具记录
        "used_tools": [],
    }


def select_route(
    state: EnterpriseGraphState,
) -> RouteName:
    route = state.get(
        "route"
    )

    if route == "knowledge":
        return "knowledge"

    if route == "sql":
        return "sql"

    return "chat"