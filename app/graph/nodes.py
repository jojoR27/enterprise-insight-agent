# knowledge_node是知识库业务节点   chat_node是普通闲聊节点

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.runtime import Runtime

from app.agents.knowledge_agent import (
    create_knowledge_agent,
)
from app.agents.sales_agent import (
    create_sales_agent,
)
from app.agents.model import get_agent_model
from app.graph.state import (
    EnterpriseGraphContext,
    EnterpriseGraphState,
)


async def knowledge_node(
    state: EnterpriseGraphState,
    runtime: Runtime[
        EnterpriseGraphContext
    ],
) -> dict:
    agent = create_knowledge_agent(trace=runtime.context.trace,)
    result = await agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    used_tools: list[str] = []

    for message in result["messages"]:
        if (
            isinstance(message, ToolMessage)
            and message.name
            and message.name not in used_tools
        ):
            used_tools.append(
                message.name
            )

    final_message = result["messages"][-1]

    if not isinstance(
        final_message,
        AIMessage,
    ):
        raise RuntimeError(
            "Knowledge Agent 未返回最终 AIMessage"
        )

    return {
        "messages": [
            final_message
        ],
        "used_tools": used_tools,
    }


async def chat_node(
    state: EnterpriseGraphState,
) -> dict:
    model = get_agent_model()

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent。"
                    "当前节点负责普通对话。"
                    "请结合已有聊天历史自然回答。"
                )
            ),
            *state["messages"],
        ]
    )

    return {
        "messages": [
            response
        ],
        "used_tools": [],
    }


async def sql_node(
    state: EnterpriseGraphState,
    runtime: Runtime[
        EnterpriseGraphContext
    ],
) -> dict:
    agent = create_sales_agent(trace=runtime.context.trace,)

    result = await agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    used_tools: list[str] = []

    for message in result["messages"]:
        if (
            isinstance(
                message,
                ToolMessage,
            )
            and message.name
            and message.name
            not in used_tools
        ):
            used_tools.append(
                message.name
            )

    final_message = (
        result["messages"][-1]
    )

    if not isinstance(
        final_message,
        AIMessage,
    ):
        raise RuntimeError(
            "Sales Agent 未返回最终 AIMessage"
        )

    return {
        "messages": [
            final_message
        ],
        "used_tools": used_tools,
    }


async def hybrid_node(
    state: EnterpriseGraphState,
    runtime: Runtime[
        EnterpriseGraphContext
    ],
) -> dict:

    # =========================
    # 1. 调用知识库 Agent
    # =========================
    knowledge_agent = create_knowledge_agent(trace=runtime.context.trace,)

    knowledge_result = await knowledge_agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    knowledge_final = (
        knowledge_result["messages"][-1]
    )

    if not isinstance(
        knowledge_final,
        AIMessage,
    ):
        raise RuntimeError(
            "Knowledge Agent 未返回最终 AIMessage"
        )

    # =========================
    # 2. 调用销售数据 Agent
    # =========================
    sales_agent = create_sales_agent(trace=runtime.context.trace,)

    sales_result = await sales_agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    sales_final = (
        sales_result["messages"][-1]
    )

    if not isinstance(
        sales_final,
        AIMessage,
    ):
        raise RuntimeError(
            "Sales Agent 未返回最终 AIMessage"
        )

    # =========================
    # 3. 收集实际调用过的工具
    # =========================
    used_tools: list[str] = []

    for message in (
        knowledge_result["messages"]
        + sales_result["messages"]
    ):
        if (
            isinstance(
                message,
                ToolMessage,
            )
            and message.name
            and message.name
            not in used_tools
        ):
            used_tools.append(
                message.name
            )

    # =========================
    # 4. 找到本轮用户原始问题
    # =========================
    user_question = ""

    for message in reversed(
        state["messages"]
    ):
        if isinstance(
            message,
            HumanMessage,
        ):
            user_question = str(
                message.content
            )
            break

    # =========================
    # 5. 综合两个 Agent 的结果
    # =========================
    model = get_agent_model()

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent "
                    "中的综合分析节点。\n\n"

                    "当前已经有两个专业 Agent "
                    "完成了查询：\n"
                    "1. Knowledge Agent："
                    "负责企业知识库、员工制度、"
                    "报销、年假等内容。\n"
                    "2. Sales Agent："
                    "负责销售额、销量、地区、"
                    "日期、渠道等结构化经营数据。\n\n"

                    "你的任务是根据用户原始问题，"
                    "将两个 Agent 的结果整理成"
                    "一个完整、准确、自然的回答。\n\n"

                    "必须遵守：\n"
                    "1. 不得编造两个 Agent "
                    "没有提供的信息。\n"
                    "2. 销售金额、销量、日期等数字"
                    "必须严格使用 Sales Agent "
                    "返回的数据。\n"
                    "3. 企业制度、报销、年假等内容"
                    "必须严格依据 Knowledge Agent "
                    "返回的结果。\n"
                    "4. 如果某一部分无法确定，"
                    "明确说明该部分无法确定。\n"
                    "5. 不要向用户解释内部 Agent "
                    "调用过程，直接给最终答案。"
                )
            ),
            HumanMessage(
                content=(
                    f"用户原始问题：\n"
                    f"{user_question}\n\n"

                    f"【知识库查询结果】\n"
                    f"{knowledge_final.content}\n\n"

                    f"【销售数据查询结果】\n"
                    f"{sales_final.content}"
                )
            ),
        ]
    )

    return {
        "messages": [
            response
        ],
        "used_tools": used_tools,
    }