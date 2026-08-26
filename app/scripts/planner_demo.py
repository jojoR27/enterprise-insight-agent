import asyncio

from app.planner.planner import (
    plan_request,
)


async def main() -> None:
    questions = [
        "按地区统计销售额，哪个地区最高？",

        "员工报销最迟多久提交？",

        (
            "统计每个渠道销售额占总销售额的比例，"
            "同时告诉我员工报销最迟多久提交？"
        ),

        "你好，介绍一下你自己。",
    ]

    for index, question in enumerate(
        questions,
        start=1,
    ):
        print()
        print("=" * 70)

        print(
            f"Case {index}"
        )

        print(
            f"用户：{question}"
        )

        print()

        decision = await plan_request(
            question
        )

        print(
            decision.model_dump_json(
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )