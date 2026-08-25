from app.text2sql.schema_registry import (
    get_allowed_columns,
    get_allowed_tables,
    get_schema_prompt,
)


def main():
    print(
        "========== Allowed Tables =========="
    )

    print(
        get_allowed_tables()
    )

    print()

    print(
        "========== Allowed Columns =========="
    )

    print(
        get_allowed_columns(
            "sales_records"
        )
    )

    print()

    print(
        "========== Schema Prompt =========="
    )

    print(
        get_schema_prompt()
    )


if __name__ == "__main__":
    main()