# 这是一套Agent运行日志追踪器  给agent做流水帐
# 用来记录 Agent 每一步动作、耗时、成功失败情况。

from __future__ import annotations

import time
import uuid

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    """
    Agent 执行过程中的一个步骤。
    """

    name: str
    category: str

    started_at: float
    finished_at: float | None = None

    latency_ms: float | None = None

    success: bool = True
    error: str | None = None

    metadata: dict = Field(default_factory=dict)


class AgentTrace(BaseModel):
    """
    一次完整 Agent 请求的执行轨迹。
    """

    trace_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex
    )

    thread_id: str | None = None

    started_at: float = Field(
        default_factory=time.perf_counter
    )

    finished_at: float | None = None

    latency_ms: float | None = None

    steps: list[TraceStep] = Field(
        default_factory=list
    )

    def start_step(
        self,
        *,
        name: str,
        category: str,
        metadata: dict | None = None,
    ) -> TraceStep:
        step = TraceStep(
            name=name,
            category=category,
            started_at=time.perf_counter(),
            metadata=metadata or {},
        )

        self.steps.append(step)

        return step

    def finish_step(
        self,
        step: TraceStep,
        *,
        success: bool = True,
        error: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        finished_at = time.perf_counter()

        step.finished_at = finished_at

        step.latency_ms = round(
            (finished_at - step.started_at) * 1000,
            2,
        )

        step.success = success
        step.error = error

        if metadata:
            step.metadata.update(metadata)

    def finish(self) -> None:
        finished_at = time.perf_counter()

        self.finished_at = finished_at

        self.latency_ms = round(
            (finished_at - self.started_at) * 1000,
            2,
        )