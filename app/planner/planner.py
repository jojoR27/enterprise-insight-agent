from functools import lru_cache
from typing import Literal

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)
from app.agents.model import get_structured_base_model

PlannerMode = Literal["chat","single","multi"]
# 后续增加的agent在这里列出来
PlannerTarget = Literal["knowledge","sales",]


class PlannerTask(BaseModel):
    target: PlannerTarget = Field(
        description=(
            "负责执行该子任务的 Agent。"
            "knowledge 表示企业知识库 Agent；"
            "sales 表示销售数据分析 Agent。"
        )
    )

    instruction: str = Field(
        min_length=1,
        description=(
            "交给目标 Agent 的完整、独立、可执行指令。"
            "必须保留用户问题中的关键条件，"
            "不得自行补充用户没有提供的业务条件。"
        ),
    )


class PlannerDecision(BaseModel):
    mode: PlannerMode = Field(
        description=(
            "chat：无需调用专业 Agent；"
            "single：只需要一个专业 Agent；"
            "multi：需要多个专业 Agent 协作。"
        )
    )

    targets: list[PlannerTarget] = Field(
        default_factory=list,
        description=(
            "本次请求需要调用的专业 Agent 列表。"
            "普通聊天时必须为空列表。"
        ),
    )

    tasks: list[PlannerTask] = Field(
        default_factory=list,
        description=(
            "已经拆分好的 Agent 子任务列表。"
            "每个 target 最多出现一次。"
        ),
    )

    reason: str = Field(
        description="生成当前任务计划的简短原因。"
    )

    # 用于检验planner_agent做出规划的合理性
    @model_validator(mode="after")
    def validate_plan(self):
        task_targets = [
            task.target
            for task in self.tasks
        ]

        # 可以合并的原子操作 合并给对应agent
        if len(task_targets) != len(set(task_targets)):
            raise ValueError("同一个 Agent 不能重复生成多个任务")

        # targets 与 tasks 必须一一对应
        if set(task_targets) != set(self.targets):
            raise ValueError("targets 必须与 tasks 中的 target 完全一致")

        # 普通聊天不需要专业 Agent
        if self.mode == "chat":
            if self.targets or self.tasks:
                raise ValueError("chat 模式不能包含 Agent targets 或 tasks")

        # 单 Agent
        elif self.mode == "single":
            if (len(self.targets) != 1or len(self.tasks) != 1):
                raise ValueError("single 模式必须且只能包含一个 Agent 任务")

        # 多 Agent
        elif self.mode == "multi":
            if len(self.targets) < 2:
                raise ValueError("multi 模式至少需要两个 Agent")

        return self


    def get_task(self,target: PlannerTarget) -> str | None:
        """
        根据 Agent 名称获取 Planner
        为它拆分出的具体任务。
        """
        for task in self.tasks:
            if task.target == target:
                return task.instruction

        return None

# 为什么要封装一层 `get_planner_model()`，而不直接调用
# get_structured_base_model()它返回一个基础 ChatOpenAI LLM对象，只是配置好了api‑key、base_url、模型名称、关闭 thinking 等底层参数。
# 它没有任何结构化输出绑定，就是一个普通聊天模型。
# `.with_structured_output()` 会生成一个包装后的新可运行对象，调用之后得到的不再是原生ChatOpenAI，而是LangChain封装出来的Runnable。
# 这个runnable被改造的行为有：自动采用function‑calling工具、强制大模型输出符合PlannerDecision的JSON、自动把JSON解析成Pydantic对象、同时保存解析错误原始返回消息。
@lru_cache
def get_planner_model():
    """
    Planner 使用结构化输出模型。

    这里复用 Router 的基础模型，
    因为它已经关闭 thinking，
    可以稳定使用 function_calling。
    """

    model = get_structured_base_model()

    return model.with_structured_output(
        PlannerDecision,
        method="function_calling",
        include_raw=True,
    )


async def plan_request(question: str) -> PlannerDecision:
    """
    根据用户问题生成Agent执行计划。
    """
    question = question.strip()

    if not question:raise ValueError("Planner question 不能为空")

    planner_model = get_planner_model()
    messages = [
        SystemMessage(
            content=(
                "你是 Enterprise Insight Agent 的 Planner。\n\n"

                "你的职责不是回答用户问题，"
                "而是判断这个请求需要哪些专业 Agent，"
                "并把请求拆成可以独立执行的子任务。\n\n"

                "当前可用专业 Agent：\n"

                "1. knowledge：企业内部知识库。"
                "负责员工手册、公司制度、年假、"
                "报销、考勤、培训、信息安全、"
                "内部流程等问题。\n"

                "2. sales：销售数据分析。"
                "负责销售额、销量、地区、产品、"
                "渠道、日期范围、占比、排名、趋势、"
                "经营统计等结构化销售数据问题。\n\n"

                "规划规则：\n"

                "1. 如果不需要任何专业 Agent，"
                "例如普通寒暄、通用聊天、"
                "询问当前对话历史、询问自己刚才说过什么、"
                "询问上一条问题或上一轮回答，"
                "mode=chat，targets=[]，tasks=[]。\n"

                "2. 只需要一个专业 Agent 时，"
                "mode=single。\n"

                "3. 同一个请求同时需要 knowledge "
                "和 sales 时，mode=multi，"
                "并分别生成两个独立子任务。\n"

                "4. 只选择真正需要的 Agent，"
                "不要为了凑数量调用无关 Agent。\n"

                "5. 每个子任务必须完整、自包含，"
                "让对应 Agent 不看原始问题"
                "也知道自己需要完成什么。\n"

                "6. 必须保留用户已经明确给出的"
                "地区、产品、渠道、日期、"
                "统计口径等条件。\n"

                "7. 不得编造用户没有提供的"
                "条件或业务事实。\n"

                "8. knowledge 子任务只负责知识库内容；"
                "sales 子任务只负责销售数据分析，"
                "不要把两个领域混在同一个子任务里。\n"

                "9. 你只输出任务计划，"
                "不回答问题本身。"

                "10. 无论最终判断为 chat、single 还是 multi，"
                "都必须返回完整的 PlannerDecision 结构化结果，"
                "绝不能直接回答用户，也不能返回空结果。\n"
            )
        ),
        HumanMessage(
            content=(
                "请为下面的用户请求生成执行计划：\n\n"
                f"{question}"
            )
        ),
    ]

    result = await planner_model.ainvoke(messages)
    decision = result.get("parsed")

    if decision is not None:
        return decision

    parsing_error = result.get("parsing_error")

    raw = result.get("raw")

    raise RuntimeError(
        "Planner 未返回有效的结构化结果。"
        f" parsing_error={parsing_error!r},"
        f" raw={raw!r}"
    )