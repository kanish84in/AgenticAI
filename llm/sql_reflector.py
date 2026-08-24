import re
import time

from typing import Any

from ollama import Client

from pydantic import BaseModel

from app.config import (
    OLLAMA_HOST,
    OLLAMA_SQL_MODEL
)


# =====================================================
# Ollama
# =====================================================

client = Client(
    host=OLLAMA_HOST,
    timeout=None
)


# =====================================================
# Public Reflection Result
# =====================================================

class SQLReflection(BaseModel):

    approved: bool

    score: float

    feedback: str


# =====================================================
# Normalize SQL
# =====================================================

def normalize_sql(
    sql: str
) -> str:

    if not sql:

        return ""

    return re.sub(
        r"\s+",
        " ",
        sql.lower().strip()
    )


# =====================================================
# Extract requested TOP N
# =====================================================

def extract_top_n(
    question: str
):

    if not question:

        return None


    match = re.search(
        r"\btop\s+(\d+)\b",
        question,
        flags=re.IGNORECASE
    )


    if not match:

        return None


    return int(
        match.group(1)
    )


# =====================================================
# Extract SQL LIMIT
# =====================================================

def extract_limit(
    sql: str
):

    match = re.search(
        r"\blimit\s+(\d+)\b",
        sql,
        flags=re.IGNORECASE
    )


    if not match:

        return None


    return int(
        match.group(1)
    )


# =====================================================
# Extract SQL Tables
# =====================================================

def extract_sql_tables(
    sql: str
) -> set[str]:

    tables = set()


    matches = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
        sql,
        flags=re.IGNORECASE
    )


    for table in matches:

        tables.add(
            table
        )


    return tables


# =====================================================
# Metric Formula Check
#
# This does not require the SQL expression to have
# identical whitespace.
#
# It checks whether the important components of the
# authoritative metric are present.
# =====================================================

def metric_formula_matches(
    sql: str,
    expression: str
) -> bool:

    if not expression:

        return True


    sql_normalized = (
        normalize_sql(
            sql
        )
    )


    expression_normalized = (
        normalize_sql(
            expression
        )
    )


    # -------------------------------------------------
    # Aggregate function
    # -------------------------------------------------

    aggregate_match = re.search(
        r"\b(sum|avg|count|min|max)\s*\(",
        expression_normalized,
        flags=re.IGNORECASE
    )


    if aggregate_match:

        aggregate_function = (
            aggregate_match.group(1)
        )


        if not re.search(
            rf"\b{aggregate_function}\s*\(",
            sql_normalized,
            flags=re.IGNORECASE
        ):

            return False


    # -------------------------------------------------
    # Table.Column references
    # -------------------------------------------------

    references = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\."
        r"[A-Za-z_][A-Za-z0-9_]*\b",
        expression
    )


    for reference in references:

        if (
            reference.lower()
            not in
            sql_normalized
        ):

            return False


    return True


# =====================================================
# Deterministic Reflection
# =====================================================

def deterministic_reflection(
    question: str,
    sql: str,
    semantic_context: dict[str, Any],
    unit_tests_ok: bool,
    validation_ok: bool
) -> SQLReflection:

    issues = []

    score = 1.0


    # =================================================
    # Unit tests
    # =================================================

    if not unit_tests_ok:

        issues.append(
            "SQL unit tests failed."
        )

        score -= 0.40


    # =================================================
    # Database validation
    # =================================================

    if not validation_ok:

        issues.append(
            "Database validation failed."
        )

        score -= 0.30


    # =================================================
    # SQL existence
    # =================================================

    if not sql:

        issues.append(
            "Generated SQL is empty."
        )

        score -= 0.50


    # =================================================
    # SELECT / WITH
    # =================================================

    if sql and not re.match(
        r"^\s*(SELECT|WITH)\b",
        sql,
        flags=re.IGNORECASE
    ):

        issues.append(
            "Query is not a SELECT/WITH statement."
        )

        score -= 0.40


    # =================================================
    # Placeholder detection
    # =================================================

    if (
        "..."
        in
        sql
        or
        "…"
        in
        sql
    ):

        issues.append(
            "SQL contains incomplete content."
        )

        score -= 0.50


    # =================================================
    # TOP N
    # =================================================

    expected_limit = (
        extract_top_n(
            question
        )
    )


    if expected_limit is not None:

        actual_limit = (
            extract_limit(
                sql
            )
        )


        if (
            actual_limit
            !=
            expected_limit
        ):

            issues.append(
                (
                    f"Expected LIMIT "
                    f"{expected_limit}, "
                    f"found {actual_limit}."
                )
            )

            score -= 0.20


    # =================================================
    # Metric Validation
    # =================================================

    metrics = (
        semantic_context.get(
            "metrics",
            []
        )
    )


    for metric in metrics:

        expression = (
            metric.get(
                "expression"
            )
        )


        metric_name = (
            metric.get(
                "name",
                "metric"
            )
        )


        if not metric_formula_matches(
            sql,
            expression
        ):

            issues.append(
                (
                    f"SQL does not appear to use "
                    f"the authoritative "
                    f"{metric_name} formula."
                )
            )

            score -= 0.25


    # =================================================
    # Metric-required tables
    # =================================================

    sql_tables = (
        extract_sql_tables(
            sql
        )
    )


    metric_tables = set(
        semantic_context.get(
            "metric_tables",
            []
        )
    )


    missing_metric_tables = (
        metric_tables
        -
        sql_tables
    )


    if missing_metric_tables:

        issues.append(
            (
                "SQL is missing metric tables: "
                +
                ", ".join(
                    sorted(
                        missing_metric_tables
                    )
                )
            )
        )

        score -= 0.20


    # =================================================
    # Keep score between 0 and 1
    # =================================================

    score = max(
        0.0,
        min(
            1.0,
            score
        )
    )


    # =================================================
    # High-confidence automatic approval
    # =================================================

    approved = (

        len(
            issues
        )
        ==
        0

        and

        score
        >=
        0.95
    )


    if approved:

        feedback = (
            "Deterministic reflection passed."
        )

    else:

        feedback = (
            "; ".join(
                issues
            )
            or
            "Additional semantic review required."
        )


    return SQLReflection(

        approved=
            approved,

        score=
            score,

        feedback=
            feedback
    )


# =====================================================
# Build Minimal Reflection Context
#
# Do NOT send the complete schema again.
#
# Reflection only needs:
# concepts
# metrics
# tables
# joins
# =====================================================

def build_reflection_context(
    semantic_context: dict[str, Any]
) -> str:

    lines = []


    concepts = (
        semantic_context.get(
            "concepts",
            []
        )
    )


    if concepts:

        lines.append(
            "Business concepts:"
        )


        for concept in concepts:

            lines.append(
                f"- {concept.get('name')}"
            )


    metrics = (
        semantic_context.get(
            "metrics",
            []
        )
    )


    if metrics:

        lines.append(
            "\nAuthoritative metrics:"
        )


        for metric in metrics:

            lines.append(
                (
                    f"- {metric.get('name')}: "
                    f"{metric.get('expression')}"
                )
            )


    tables = (
        semantic_context.get(
            "tables",
            []
        )
    )


    if tables:

        lines.append(
            "\nAllowed tables:"
        )

        lines.append(
            ", ".join(
                tables
            )
        )


    joins = (
        semantic_context.get(
            "joins",
            []
        )
    )


    if joins:

        lines.append(
            "\nAllowed joins:"
        )


        for join in joins:

            lines.append(
                (
                    f"- "
                    f"{join.get('source_table')}."
                    f"{join.get('source_column')} = "
                    f"{join.get('target_table')}."
                    f"{join.get('target_column')}"
                )
            )


    return "\n".join(
        lines
    )


# =====================================================
# LLM Fallback Reflection
#
# qwen2.5-coder:3b is used instead of qwen3:4b.
#
# Response format:
#
# APPROVE|0.95|reason
#
# or
#
# REJECT|0.70|reason
# =====================================================

def llm_reflection(
    question: str,
    sql: str,
    semantic_context: dict[str, Any]
) -> SQLReflection:

    context = (
        build_reflection_context(
            semantic_context
        )
    )


    system_prompt = """
You are reviewing a SQLite query.

Check only:

1. Does the SQL answer the user's question?
2. Does it use the supplied authoritative metric?
3. Does it use valid supplied tables and joins?
4. Does top-N use the correct ordering and LIMIT?

Respond exactly:

APPROVE|score|short reason

or

REJECT|score|short reason

Score must be between 0 and 1.

Do not provide reasoning steps.
"""


    user_prompt = f"""
QUESTION
========
{question}

SEMANTIC CONTEXT
================
{context}

SQL
===
{sql}
"""


    print(
        "\nUsing LLM reflection fallback...",
        flush=True
    )


    start = (
        time.time()
    )


    response = client.chat(

        model=
            OLLAMA_SQL_MODEL,

        messages=[

            {
                "role":
                    "system",

                "content":
                    system_prompt
            },

            {
                "role":
                    "user",

                "content":
                    user_prompt
            }
        ],

        keep_alive=
            "30m",

        options={

            "temperature":
                0,

            "num_ctx":
                2048,

            "num_predict":
                80
        }
    )


    elapsed = (
        time.time()
        -
        start
    )


    output = (
        response
        .message
        .content
        .strip()
    )


    print(
        (
            f"Reflection fallback time: "
            f"{elapsed:.2f} seconds"
        ),
        flush=True
    )


    print(
        (
            "Reflection fallback output: "
            f"{output}"
        ),
        flush=True
    )


    # =================================================
    # Remove markdown if model adds it
    # =================================================

    output = re.sub(
        r"^```.*?\n",
        "",
        output
    )


    output = re.sub(
        r"\n```$",
        "",
        output
    )


    parts = (
        output.split(
            "|",
            2
        )
    )


    if len(
        parts
    ) != 3:

        return SQLReflection(

            approved=
                False,

            score=
                0.5,

            feedback=
                (
                    "Reflection fallback returned "
                    "an unexpected format."
                )
        )


    decision = (
        parts[0]
        .strip()
        .upper()
    )


    try:

        score = float(
            parts[1].strip()
        )

    except ValueError:

        score = (
            0.5
        )


    score = max(
        0.0,
        min(
            1.0,
            score
        )
    )


    feedback = (
        parts[2]
        .strip()
    )


    return SQLReflection(

        approved=
            decision
            ==
            "APPROVE",

        score=
            score,

        feedback=
            feedback
    )


# =====================================================
# Main Reflection Function
# =====================================================

def reflect_on_sql(
    question: str,
    sql: str,
    semantic_context: dict[str, Any],
    unit_tests_ok: bool = True,
    validation_ok: bool = True
) -> SQLReflection:

    # =================================================
    # Stage 1:
    # deterministic reflection
    # =================================================

    deterministic_result = (
        deterministic_reflection(

            question=
                question,

            sql=
                sql,

            semantic_context=
                semantic_context,

            unit_tests_ok=
                unit_tests_ok,

            validation_ok=
                validation_ok
        )
    )


    print(
        "\nDETERMINISTIC REFLECTION"
    )


    print(
        (
            f"Approved: "
            f"{deterministic_result.approved}"
        )
    )


    print(
        (
            f"Score: "
            f"{deterministic_result.score}"
        )
    )


    print(
        (
            f"Feedback: "
            f"{deterministic_result.feedback}"
        )
    )


    # =================================================
    # High confidence:
    # skip the LLM entirely.
    # =================================================

    if deterministic_result.approved:

        print(
            (
                "LLM reflection skipped - "
                "high-confidence deterministic "
                "checks passed."
            )
        )


        return (
            deterministic_result
        )


    # =================================================
    # Stage 2:
    # LLM fallback only when necessary
    # =================================================

    return (
        llm_reflection(

            question=
                question,

            sql=
                sql,

            semantic_context=
                semantic_context
        )
    )