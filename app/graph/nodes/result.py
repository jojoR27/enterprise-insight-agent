from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from app.agents.model import get_agent_model
from app.graph.state import (
    EnterpriseGraphState,
    ResultMode,
    WorkerResult,
)


def get_ordered_results(state: EnterpriseGraphState,) -> list[WorkerResult]:
    """
    并行 Worker 的完成顺序不一定固定。
    按 Planner targets 的顺序重新排列，
    让最终输出更稳定。
    """
    results = state.get("worker_results",[],)
    targets = state.get("planner_targets",[],)
    order = {
        target: index
        for index, target in enumerate(targets)
    }

    return sorted(
        results,
        key=lambda result: order.get(result["target"],999,),
    )


def collect_worker_tools(results: list[WorkerResult],) -> list[str]:
    used_tools: list[str] = []

    for result in results:
        for tool_name in result["used_tools"]:
            if (tool_name not in used_tools):
                used_tools.append(tool_name)
    return used_tools


async def result_coordinator_node(state: EnterpriseGraphState,) -> dict:
    """
    判断：
    只有一个 Worker → 直接返回
    多个 Worker → Synthesis
    """
    results = get_ordered_results(state)

    if not results:
        raise RuntimeError("没有 Worker 执行结果")

    result_mode: ResultMode

    if len(results) == 1:
        result_mode = "direct"
    else:
        result_mode = "synthesis"

    return {
        "result_mode":result_mode,
        "used_tools":collect_worker_tools(results),
    }


def select_result_path(state: EnterpriseGraphState,) -> ResultMode:
    mode = state.get("result_mode")

    if mode not in {"direct","synthesis",}:
        raise RuntimeError(f"非法 result_mode: {mode}")
    return mode


async def direct_result_node(state: EnterpriseGraphState,) -> dict:
    """
    只有一个专业 Agent 时，
    不再额外调用一次 LLM。
    """
    results = get_ordered_results(state)

    if len(results) != 1:
        raise RuntimeError("Direct Result 必须且只能有一个 Worker Result")

    result = results[0]

    return {
        "messages": [AIMessage(content=result["content"])]
    }


async def synthesis_node(state: EnterpriseGraphState,) -> dict:
    """
    多 Agent 结果统一综合。
    """
    results = get_ordered_results(state)

    if len(results) < 2:
        raise RuntimeError("Synthesis 至少需要两个 Worker Result")

    user_question = ""

    for message in reversed(state["messages"]):
        if isinstance(message,HumanMessage,):
            user_question = str(message.content)
            break

    result_blocks = []

    for result in results:
        result_blocks.append(
            (
                f"【{result['target']} "
                f"Worker 结果】\n"
                f"{result['content']}"
            )
        )

    worker_content = "\n\n".join(result_blocks)

    model = get_agent_model()

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent "
                    "的结果综合节点。\n\n"

                    "多个专业 Worker "
                    "已经分别完成自己的任务。\n"

                    "请根据用户原始问题，"
                    "把这些 Worker 的结果"
                    "整理成完整、自然、准确的最终答案。\n\n"

                    "必须遵守：\n"
                    "1. 只能依据 Worker 返回的信息回答。\n"
                    "2. 不得编造 Worker "
                    "没有提供的数据或制度内容。\n"
                    "3. 如果不同 Worker "
                    "负责不同问题部分，"
                    "分别清晰回答。\n"
                    "4. 如果某部分 Worker "
                    "无法确定，必须明确说明。\n"
                    "5. 不向用户解释内部 Planner、"
                    "Worker、Tool 调用过程。"
                )
            ),
            HumanMessage(
                content=(
                    f"用户原始问题：\n"
                    f"{user_question}\n\n"
                    f"{worker_content}"
                )
            ),
        ]
    )

    return {"messages": [response]}