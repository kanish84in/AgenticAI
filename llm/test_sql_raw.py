import time

from ollama import Client

from app.config import (
    OLLAMA_HOST,
    OLLAMA_SQL_MODEL
)

from graph.semantic_retriever import (
    retrieve_semantic_context,
    semantic_context_to_text
)

from llm.sql_generator import (
    clean_sql_output
)

from database.sql_tests import (
    run_sql_unit_tests
)


# =====================================================
# Ollama Client
# =====================================================

client = Client(
    host=OLLAMA_HOST,
    timeout=None
)


# =====================================================
# Test Question
# =====================================================

question = (
    "Show top 5 listeners by income"
)


# =====================================================
# GraphRAG
# =====================================================

semantic_context = (
    retrieve_semantic_context(
        question
    )
)


schema_context = (
    semantic_context_to_text(
        semantic_context
    )
)


# =====================================================
# Prompt
# =====================================================

system_prompt = """
You are an expert SQLite database engineer.

Generate one complete executable SQLite query that
answers the user's question.

Use only the tables, columns, joins and business
metrics supplied in the database context.

Business metric definitions are authoritative.

For top-N requests:
- calculate the requested metric
- order by that metric descending
- apply LIMIT N

When aggregation is used, include every selected
non-aggregated column in GROUP BY.

Use explicit JOIN syntax.

Return only SQL.
"""


user_prompt = f"""
QUESTION
========
{question}


DATABASE AND BUSINESS CONTEXT
=============================
{schema_context}


Generate the complete executable SQLite query.
"""


# =====================================================
# Diagnostics
# =====================================================

print(
    "\nQUESTION"
)

print(
    "=" * 70
)

print(
    question
)


print(
    "\nSELECTED TABLES"
)

print(
    "=" * 70
)

print(
    semantic_context.get(
        "tables",
        []
    )
)


print(
    "\nSELECTED CONCEPTS"
)

print(
    "=" * 70
)

print(
    [
        concept.get(
            "name"
        )

        for concept
        in semantic_context.get(
            "concepts",
            []
        )
    ]
)


print(
    "\nSELECTED METRICS"
)

print(
    "=" * 70
)

print(
    [
        metric.get(
            "name"
        )

        for metric
        in semantic_context.get(
            "metrics",
            []
        )
    ]
)


print(
    "\nPROMPTING OLLAMA..."
)

print(
    f"MODEL: {OLLAMA_SQL_MODEL}"
)


# =====================================================
# Call SQL Model
# =====================================================

start_time = (
    time.time()
)


response = (
    client.chat(

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
                4096,

            "num_predict":
                400
        }
    )
)


elapsed_time = (
    time.time()
    -
    start_time
)


# =====================================================
# Extract Response
# =====================================================

raw_output = (
    response
    .message
    .content
)


# =====================================================
# Clean SQL
# =====================================================

cleaned_sql = (
    clean_sql_output(
        raw_output
    )
)


# =====================================================
# Output
# =====================================================

print(
    "\nPERFORMANCE"
)

print(
    "=" * 70
)


print(
    (
        f"Response time: "
        f"{elapsed_time:.2f} seconds"
    )
)


print(
    (
        f"Prompt tokens: "
        f"{response.prompt_eval_count}"
    )
)


print(
    (
        f"Generated tokens: "
        f"{response.eval_count}"
    )
)


print(
    "\nRAW MODEL OUTPUT"
)

print(
    "=" * 70
)

print(
    raw_output
)


print(
    "\nCLEANED SQL OUTPUT"
)

print(
    "=" * 70
)

print(
    cleaned_sql
)


# =====================================================
# Basic Diagnostics
# =====================================================

output_lower = (
    cleaned_sql.lower()
)


starts_with_sql = (

    output_lower.startswith(
        "select"
    )

    or

    output_lower.startswith(
        "with"
    )
)


contains_placeholder = (

    "..."
    in
    cleaned_sql

    or

    "…"
    in
    cleaned_sql
)


contains_limit_5 = (
    "limit 5"
    in
    output_lower
)


contains_customer = (
    "customer"
    in
    output_lower
)


contains_invoice = (
    "invoice"
    in
    output_lower
)


contains_invoice_line = (
    "invoiceline"
    in
    output_lower
)


print(
    "\nOUTPUT DIAGNOSTICS"
)

print(
    "=" * 70
)


print(
    (
        "Starts with SELECT/WITH: "
        f"{starts_with_sql}"
    )
)


print(
    (
        "Contains placeholder: "
        f"{contains_placeholder}"
    )
)


print(
    (
        "Contains LIMIT 5: "
        f"{contains_limit_5}"
    )
)


print(
    (
        "Uses Customer: "
        f"{contains_customer}"
    )
)


print(
    (
        "Uses Invoice: "
        f"{contains_invoice}"
    )
)


print(
    (
        "Uses InvoiceLine: "
        f"{contains_invoice_line}"
    )
)


# =====================================================
# Actual SQL Unit Tests
# =====================================================

test_results = (
    run_sql_unit_tests(
        question,
        cleaned_sql
    )
)


print(
    "\nSQL UNIT TESTS"
)

print(
    "=" * 70
)


for test in test_results[
    "tests"
]:

    print(
        (
            f"{test['name']}: "
            f"{test['passed']} "
            f"- "
            f"{test['message']}"
        )
    )


# =====================================================
# Final Result
# =====================================================

basic_test_passed = all(
    [

        starts_with_sql,

        not contains_placeholder,

        contains_limit_5,

        contains_customer,

        contains_invoice,

        contains_invoice_line
    ]
)


overall_passed = (

    basic_test_passed

    and

    test_results[
        "passed"
    ]
)


print(
    "\nFINAL TEST RESULT"
)

print(
    "=" * 70
)


if overall_passed:

    print(
        (
            "PASS - SQL generation, cleanup "
            "and validation all succeeded."
        )
    )


else:

    print(
        (
            "FAIL - Review the diagnostics "
            "above."
        )
    )