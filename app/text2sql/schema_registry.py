# Text-to-SQL 的 Schema Registry（数据库结构注册表）

# 第一层
# Schema Registry
# → LLM 只知道允许的表

# Schema Registry
#      │
#      ├──→ SQL Generator
#      │      告诉 LLM：
#      │      有哪些表、字段、业务含义
#      │
#      └──→ SQL Validator
#             告诉安全层：
#             哪些表、字段允许访问

from typing import Any

# 可访问的数据库表
SCHEMA_REGISTRY: dict[str, dict[str, Any]] = {
    "sales_records": {
        "description": (
            "企业销售记录表。"
            "每一行表示一条销售业务记录。"
        ),
        "columns": {
            "id": {
                "type": "integer",
                "description": "销售记录主键 ID",
            },
            "sale_date": {
                "type": "date",
                "description": (
                    "销售日期。"
                    "按天、月、季度、年份分析销售数据时"
                    "应使用该字段。"
                ),
            },
            "region": {
                "type": "varchar",
                "description": (
                    "销售地区，例如华东、华北等。"
                ),
            },
            "product_name": {
                "type": "varchar",
                "description": "销售产品名称",
            },
            "channel": {
                "type": "varchar",
                "description": (
                    "销售渠道，例如线上、线下等。"
                ),
            },
            "quantity": {
                "type": "integer",
                "description": (
                    "本条销售记录的销售数量。"
                    "统计总销量时通常使用 "
                    "SUM(quantity)。"
                ),
            },
            "unit_price": {
                "type": "numeric(12,2)",
                "description": "产品销售单价",
            },
            "revenue": {
                "type": "numeric(14,2)",
                "description": (
                    "本条销售记录对应的销售收入。"
                    "用户提到销售额、营业额、销售收入时，"
                    "通常使用 SUM(revenue)。"
                ),
            },
            "created_at": {
                "type": "timestamptz",
                "description": (
                    "数据库记录创建时间。"
                    "它不是实际销售日期。"
                    "销售时间分析应优先使用 sale_date。"
                ),
            },
        },
    },
}

# 业务规则 给LLM
BUSINESS_RULES: tuple[str, ...] = (
    "数据库使用 PostgreSQL 语法。",
    "销售额、营业额、销售收入默认指 SUM(revenue)。",
    "销量、销售数量默认指 SUM(quantity)。",
    "销售日期分析使用 sale_date，不使用 created_at。",
    "按地区统计使用 region。",
    "按产品统计使用 product_name。",
    "按渠道统计使用 channel。",
    "除非用户明确要求，否则不要把 id 当作业务统计维度。",
)

def get_allowed_tables() -> set[str]:
    return set(
        SCHEMA_REGISTRY.keys()
    )

def get_allowed_columns(table_name: str,) -> set[str]:
    table_schema = SCHEMA_REGISTRY.get(table_name)

    if table_schema is None:
        return set()

    columns = table_schema.get(
        "columns",
        {},
    )

    return set(columns.keys())


def get_schema_prompt() -> str:
    lines: list[str] = []
    lines.append("以下是你允许查询的数据库结构：")

    for (table_name,table_schema,) in SCHEMA_REGISTRY.items():
        lines.append("")
        lines.append(f"表名：{table_name}")
        lines.append("表说明："f"{table_schema['description']}")

        lines.append("字段：")

        columns = table_schema["columns"]

        for (column_name,column_schema,) in columns.items():

            lines.append(
                (
                    f"- {column_name} "
                    f"({column_schema['type']}): "
                    f"{column_schema['description']}"
                )
            )

    lines.append("")
    lines.append("业务规则：")

    for index, rule in enumerate(
        BUSINESS_RULES,
        start=1,
    ):
        lines.append(
            f"{index}. {rule}"
        )

    return "\n".join(lines)