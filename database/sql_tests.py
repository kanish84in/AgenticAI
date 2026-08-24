import re

from typing import Any


from database.db import (
    validate_sql_against_database
)


# =====================================================
# SQL Normalization
# =====================================================

def normalize_sql(
    sql: str
) -> str:

    if not sql:

        return ""


    return (
        sql
        .strip()
    )


# =====================================================
# Test 1: Read-only SQL
# =====================================================

def test_readonly(
    sql: str
) -> dict[str, Any]:

    sql = (
        normalize_sql(
            sql
        )
    )


    if not sql:

        return {

            "name":
                "readonly",

            "passed":
                False,

            "message":
                "SQL is empty."
        }


    # =================================================
    # Must begin with SELECT or WITH
    # =================================================

    if not re.match(
        r"^\s*(SELECT|WITH)\b",
        sql,
        flags=re.IGNORECASE
    ):

        return {

            "name":
                "readonly",

            "passed":
                False,

            "message":
                (
                    "Only SELECT or WITH "
                    "queries are allowed."
                )
        }


    # =================================================
    # Block write operations
    # =================================================

    blocked_keywords = [

        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE",
        "ATTACH",
        "DETACH"
    ]


    for keyword in blocked_keywords:

        pattern = (
            r"\b"
            +
            re.escape(
                keyword
            )
            +
            r"\b"
        )


        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE
        ):

            return {

                "name":
                    "readonly",

                "passed":
                    False,

                "message":
                    (
                        "SQL contains prohibited "
                        f"operation: {keyword}."
                    )
            }


    return {

        "name":
            "readonly",

        "passed":
            True,

        "message":
            "SQL is read-only."
    }


# =====================================================
# Test 2: Placeholder / Incomplete SQL
# =====================================================

def test_no_placeholders(
    sql: str
) -> dict[str, Any]:

    sql = (
        normalize_sql(
            sql
        )
    )


    sql_lower = (
        sql.lower()
    )


    invalid_patterns = [

        "...",

        "<sql>",

        "<query>",

        "sql here",

        "query here",

        "your sql",

        "select ..."
    ]


    detected = []


    for pattern in invalid_patterns:

        if (
            pattern
            in
            sql_lower
        ):

            detected.append(
                pattern
            )


    if detected:

        return {

            "name":
                "no_placeholders",

            "passed":
                False,

            "message":
                (
                    "SQL contains placeholder or "
                    "incomplete content: "
                    +
                    ", ".join(
                        detected
                    )
                )
        }


    # =================================================
    # Additional minimum-completeness test
    # =================================================

    if len(
        sql.split()
    ) < 4:

        return {

            "name":
                "no_placeholders",

            "passed":
                False,

            "message":
                (
                    "SQL appears incomplete."
                )
        }


    return {

        "name":
            "no_placeholders",

        "passed":
            True,

        "message":
            (
                "SQL contains no placeholder "
                "content."
            )
    }


# =====================================================
# Test 3: Database SQL Validity
# =====================================================

def test_database_validity(
    sql: str
) -> dict[str, Any]:

    try:

        result = (
            validate_sql_against_database(
                sql
            )
        )


        if result.get(
            "valid",
            False
        ):

            return {

                "name":
                    "database_validity",

                "passed":
                    True,

                "message":
                    (
                        "SQL is valid "
                        "against SQLite."
                    )
            }


        return {

            "name":
                "database_validity",

            "passed":
                False,

            "message":
                (
                    result.get(
                        "error"
                    )
                    or
                    "SQL validation failed."
                )
        }


    except Exception as error:

        return {

            "name":
                "database_validity",

            "passed":
                False,

            "message":
                str(
                    error
                )
        }


# =====================================================
# Extract "Top N" From Question
# =====================================================

def extract_expected_limit(
    question: str
):

    if not question:

        return None


    # Examples:
    #
    # top 5 customers
    # top 10 artists
    # top 20 tracks

    match = re.search(

        r"\btop\s+(\d+)\b",

        question,

        flags=re.IGNORECASE
    )


    if not match:

        return None


    return int(
        match.group(
            1
        )
    )


# =====================================================
# Extract LIMIT From SQL
# =====================================================

def extract_sql_limit(
    sql: str
):

    if not sql:

        return None


    match = re.search(

        r"\bLIMIT\s+(\d+)\b",

        sql,

        flags=re.IGNORECASE
    )


    if not match:

        return None


    return int(
        match.group(
            1
        )
    )


# =====================================================
# Test 4: Expected LIMIT
# =====================================================

def test_expected_limit(
    question: str,
    sql: str
) -> dict[str, Any]:

    expected_limit = (
        extract_expected_limit(
            question
        )
    )


    # =================================================
    # Question does not request top N
    # =================================================

    if (
        expected_limit
        is None
    ):

        return {

            "name":
                "expected_limit",

            "passed":
                True,

            "message":
                (
                    "Question does not request "
                    "a specific top-N LIMIT."
                )
        }


    actual_limit = (
        extract_sql_limit(
            sql
        )
    )


    # =================================================
    # LIMIT completely missing
    # =================================================

    if (
        actual_limit
        is None
    ):

        return {

            "name":
                "expected_limit",

            "passed":
                False,

            "message":
                (
                    f"Question requests top "
                    f"{expected_limit}, but SQL "
                    f"contains no LIMIT."
                )
        }


    # =================================================
    # Wrong LIMIT
    # =================================================

    if (
        actual_limit
        !=
        expected_limit
    ):

        return {

            "name":
                "expected_limit",

            "passed":
                False,

            "message":
                (
                    f"Question requests top "
                    f"{expected_limit}, but SQL "
                    f"contains LIMIT "
                    f"{actual_limit}."
                )
        }


    return {

        "name":
            "expected_limit",

        "passed":
            True,

        "message":
            (
                f"Expected LIMIT "
                f"{expected_limit}; found "
                f"LIMIT {actual_limit}."
            )
    }


# =====================================================
# Run SQL Unit Tests
# =====================================================

def run_sql_unit_tests(
    question: str,
    sql: str
) -> dict[str, Any]:

    tests = []


    # =================================================
    # 1. Read-only test
    # =================================================

    readonly_result = (
        test_readonly(
            sql
        )
    )


    tests.append(
        readonly_result
    )


    # =================================================
    # 2. Placeholder test
    # =================================================

    placeholder_result = (
        test_no_placeholders(
            sql
        )
    )


    tests.append(
        placeholder_result
    )


    # =================================================
    # 3. Database validity
    #
    # Do not execute database validation if the SQL
    # is obviously placeholder/incomplete content.
    # =================================================

    if placeholder_result[
        "passed"
    ]:

        database_result = (
            test_database_validity(
                sql
            )
        )

    else:

        database_result = {

            "name":
                "database_validity",

            "passed":
                False,

            "message":
                (
                    "Database validation skipped "
                    "because SQL contains "
                    "placeholder or incomplete "
                    "content."
                )
        }


    tests.append(
        database_result
    )


    # =================================================
    # 4. LIMIT test
    # =================================================

    limit_result = (
        test_expected_limit(
            question,
            sql
        )
    )


    tests.append(
        limit_result
    )


    # =================================================
    # Final Status
    # =================================================

    passed = all(

        test[
            "passed"
        ]

        for test
        in tests
    )


    # =================================================
    # Aggregate Failure Messages
    # =================================================

    failed_messages = [

        test[
            "message"
        ]

        for test
        in tests

        if not test[
            "passed"
        ]
    ]


    error = (
        "\n".join(
            failed_messages
        )
    )


    return {

        "passed":
            bool(
                passed
            ),

        "tests":
            tests,

        "error":
            error
    }