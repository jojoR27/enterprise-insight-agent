# AgentLoop（while 反复思考‑工具调用）封装在create_agent返回的runnable内部。
from langchain.agents import create_agent

from app.agents.model import get_agent_model
from app.agents.tools.knowledge_tool import (
    create_knowledge_tool,
)
from app.observability.trace import AgentTrace


def create_knowledge_agent(trace: AgentTrace | None = None):
    knowledge_tool = create_knowledge_tool(
        k=3,
        min_similarity=0.6,
        trace = trace
    )

    model = get_agent_model()

    return create_agent(
        model=model,
        tools=[
            knowledge_tool,
        ],
        system_prompt=(
            "你是 Enterprise Insight Agent，"
            "负责回答企业内部知识相关问题。\n\n"

            "规则：\n"
            "1. 用户询问企业内部制度、员工手册、"
            "年假、考勤、报销、培训、信息安全等内容时，"
            "优先调用 search_enterprise_knowledge。\n"

            "2. 对于企业内部问题，"
            "不得只依赖模型自身知识进行猜测。\n"

            "3. 如果知识库工具没有返回有效资料，"
            "明确告诉用户当前知识库无法确定。\n"

            "4. 普通寒暄或通用问题，"
            "没有必要调用知识库工具。\n"

            "5. 使用知识库回答时，"
            "尽量说明答案来自哪个文件。"
        ),
    )