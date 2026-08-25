from app.text2sql.sql_validator import (
    validate_sql,
)

def print_result(title: str,sql: str,):
    print()
    print("=" * 70)

    print(title)

    print("=" * 70)

    print("SQL:")

    print(sql)

    result = validate_sql(sql)

    print()

    print("is_valid:")

    print(result.is_valid)

    print()

    print("errors:")

    print(result.errors)

    print()

    print("warnings:")

    print(result.warnings)

    print()

    print("tables:")

    print(result.referenced_tables)

    print()

    print("columns:")

    print(result.referenced_columns)

    print()

    print("normalized_sql:")

    print(result.normalized_sql)


def main():
    # 1. 正常 SQL
    print_result(
        "正常销售统计",
        """
        SELECT
            sale_date,
            SUM(revenue) AS total_revenue
        FROM sales_records
        GROUP BY sale_date
        ORDER BY total_revenue DESC
        LIMIT 1
        """,
    )

    # 2. DELETE
    print_result(
        "危险 DELETE",
        """
        DELETE
        FROM sales_records
        """,
    )

    # 3. 多语句注入
    print_result(
        "多 SQL 注入",
        """
        SELECT
            region
        FROM sales_records;

        DELETE
        FROM sales_records;
        """,
    )

    # 4. 非白名单表
    print_result(
        "访问非法表",
        """
        SELECT
            username
        FROM users
        """,
    )

    # 5. 非白名单字段
    print_result(
        "访问非法字段",
        """
        SELECT
            password
        FROM sales_records
        """,
    )

    # 6. SELECT *
    print_result(
        "SELECT 星号",
        """
        SELECT
            *
        FROM sales_records
        """,
    )


if __name__ == "__main__":
    main()