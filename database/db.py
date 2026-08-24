import re
import sqlite3

from app.config import SQLITE_DB_PATH


BLOCKED_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "VACUUM",
    "PRAGMA",
}


def get_connection():
    """
    Open Chinook in read-only mode.
    """

    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {SQLITE_DB_PATH}"
        )

    database_uri = (
        SQLITE_DB_PATH.resolve().as_uri()
        + "?mode=ro"
    )

    return sqlite3.connect(
        database_uri,
        uri=True
    )


def get_schema_text():
    """
    Extract tables, columns and foreign keys
    from SQLite.

    This schema will be passed to the LLM.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        schema_parts = []

        for table in tables:

            schema_parts.append(
                f"\nTABLE: {table}"
            )

            # Get columns
            columns = connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()

            schema_parts.append("COLUMNS:")

            for column in columns:

                column_name = column[1]
                column_type = column[2]
                primary_key = column[5]

                description = (
                    f"- {column_name} {column_type}"
                )

                if primary_key:
                    description += " PRIMARY KEY"

                schema_parts.append(
                    description
                )

            # Foreign keys
            foreign_keys = connection.execute(
                f'PRAGMA foreign_key_list("{table}")'
            ).fetchall()

            if foreign_keys:

                schema_parts.append(
                    "FOREIGN KEYS:"
                )

                for fk in foreign_keys:

                    referenced_table = fk[2]
                    source_column = fk[3]
                    referenced_column = fk[4]

                    schema_parts.append(
                        f"- {source_column} -> "
                        f"{referenced_table}."
                        f"{referenced_column}"
                    )

        return "\n".join(schema_parts)

    finally:

        connection.close()


def validate_readonly_sql(sql: str):
    """
    Basic safety validation.

    This is intentionally simple.
    We will replace it with a real SQL
    validation agent later.
    """

    cleaned_sql = sql.strip()

    if not cleaned_sql:
        raise ValueError(
            "Generated SQL is empty."
        )

    # Remove final semicolon
    if cleaned_sql.endswith(";"):
        cleaned_sql = cleaned_sql[:-1]

    # Prevent multiple statements
    if ";" in cleaned_sql:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    upper_sql = cleaned_sql.upper()

    if not (
        upper_sql.startswith("SELECT")
        or upper_sql.startswith("WITH")
    ):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    for keyword in BLOCKED_SQL_KEYWORDS:

        if re.search(
            rf"\b{keyword}\b",
            upper_sql
        ):
            raise ValueError(
                f"Blocked SQL keyword: {keyword}"
            )

    return cleaned_sql


def execute_query(
    sql: str,
    max_rows: int = 100
):
    """
    Execute a read-only SQL query.
    """

    sql = validate_readonly_sql(sql)

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(sql)

        column_names = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchmany(
            max_rows
        )

        results = []

        for row in rows:

            results.append(
                dict(
                    zip(
                        column_names,
                        row
                    )
                )
            )

        return {
            "columns": column_names,
            "rows": results,
            "row_count": len(results)
        }

    finally:

        connection.close()

def validate_sql_against_database(
    sql: str
):
    """
    Validate SQL using SQLite query planning.

    This catches:
    - nonexistent tables
    - nonexistent columns
    - invalid syntax
    - invalid joins

    without executing the full query.
    """

    cleaned_sql = (
        validate_readonly_sql(
            sql
        )
    )


    connection = get_connection()


    try:

        cursor = (
            connection.cursor()
        )


        cursor.execute(
            "EXPLAIN QUERY PLAN "
            + cleaned_sql
        )


        cursor.fetchall()


        return {
            "valid": True,
            "sql": cleaned_sql,
            "error": ""
        }


    except Exception as error:

        return {
            "valid": False,
            "sql": cleaned_sql,
            "error": str(error)
        }


    finally:

        connection.close()