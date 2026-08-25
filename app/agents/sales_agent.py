from langchain.agents import (
    create_agent,
)
from app.agents.model import (
    get_agent_model,
)
from app.agents.tools.sales_tool import (
    create_sales_tool,
)


def create_sales_agent():
    sales_tool = create_sales_tool()

    model = get_agent_model()

    return create_agent(
        model=model,
        # 后面在这加工具
        tools=[
            sales_tool,
        ],
        system_prompt=(
            "你是 Enterprise Insight Agent "
            "中的销售数据分析 Agent。\n\n"

            "你负责回答企业销售数据问题。\n"

            "规则：\n"
            "1. 涉及销售额、销量、地区、产品、"
            "渠道、日期范围等业务数据时，"
            "必须调用 query_sales_data。\n"

            "2. 禁止根据模型自身知识猜测"
            "任何销售数字。\n"

            "3. Tool 返回的数据是唯一可信"
            "的销售数据来源。\n"

            "4. 如果 Tool 没有返回数据，"
            "明确告诉用户当前条件下没有数据。\n"

            "5. 回答时把数据整理成人类容易"
            "理解的形式，不要直接复制 JSON。\n"

            "6. 金额、销量等数字必须严格"
            "按照 Tool 返回结果回答。"
        ),
    )