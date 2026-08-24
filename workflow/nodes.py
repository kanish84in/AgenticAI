from database.db import (
    execute_query,
    get_schema_text,
    validate_sql_against_database
)

from graph.semantic_retriever import (
    retrieve_semantic_context,
    semantic_context_to_text
)

from llm.intent_planner import (
    classify_and_plan
)

from llm.sql_generator import (
    generate_sql
)

from workflow.state import (
    AgentState
)

from llm.tool_selector import (
    select_tools
)

from database.sql_tests import (
    run_sql_unit_tests
)

from llm.sql_reflector import (
    reflect_on_sql
)


# =====================================================
# NODE 1
# Intent + Planning
# =====================================================

def intent_planner_node(
    state: AgentState
):

    question = state["question"]

    result = classify_and_plan(
        question
    )

    return {

        "intent":
            result.intent,

        "plan":
            result.plan,

        "trace": [
            f"Intent classified as: "
            f"{result.intent}",

            "Execution plan created"
        ]
    }


# =====================================================
# NODE 2
# Semantic Retrieval
# =====================================================

def semantic_retrieval_node(
    state: AgentState
):

    question = (
        state["question"]
    )


    semantic_context = (
        retrieve_semantic_context(
            question
        )
    )


    # -------------------------------------
    # GraphRAG success
    # -------------------------------------

    if semantic_context.get(
        "tables"
    ):

        schema_context = (
            semantic_context_to_text(
                semantic_context
            )
        )

        retrieval_mode = (
            "hybrid_graph_rag"
        )


    # -------------------------------------
    # Fallback
    # -------------------------------------

    else:

        schema_context = (
            get_schema_text()
        )

        retrieval_mode = (
            "full_schema_fallback"
        )


    return {

        "semantic_context":
            semantic_context,

        "schema_context":
            schema_context,

        "retrieval_mode":
            retrieval_mode,

        "trace": [
            f"Semantic retrieval completed "
            f"using {retrieval_mode}",

            f"Selected tables: "
            f"{semantic_context.get('tables', [])}"
        ]
    }


# =====================================================
# NODE 3
# SQL Generation
# =====================================================

def sql_generation_node(
    state: AgentState
):

    generation = (
        generate_sql(

            question=
                state["question"],

            schema=
                state[
                    "schema_context"
                ]
        )
    )


    return {

        "generated_sql":
            generation.sql,

        "sql_explanation":
            generation.explanation,

        "validation_ok":
            False,

        "validation_error":
            "",

        "trace": [
            "SQL generated"
        ]
    }


# =====================================================
# NODE 4
# SQL Validation
# =====================================================

def sql_validation_node(
    state: AgentState
):

    result = (
        validate_sql_against_database(
            state[
                "generated_sql"
            ]
        )
    )


    if result["valid"]:

        return {

            "generated_sql":
                result["sql"],

            "validation_ok":
                True,

            "validation_error":
                "",

            "trace": [
                "SQL validation successful"
            ]
        }


    return {

        "validation_ok":
            False,

        "validation_error":
            result["error"],

        "trace": [
            "SQL validation failed: "
            + result["error"]
        ]
    }


# =====================================================
# NODE 5
# SQL Correction
# =====================================================

def sql_correction_node(
    state: AgentState
):

    retry_count = (
        state.get(
            "retry_count",
            0
        )
        + 1
    )


    error = (
        state.get(
            "unit_test_error"
        )
        or
        state.get(
            "validation_error"
        )
        or
        state.get(
            "reflection_feedback"
        )
        or
        state.get(
            "execution_error"
        )
        or
        "Unknown SQL error"
    )

    feedback = f"""
Previous SQL:

{state.get("generated_sql", "")}

Error:

{error}

Use the provided database context to correct
the SQL query.
"""


    generation = (
        generate_sql(

            question=
                state[
                    "question"
                ],

            schema=
                state[
                    "schema_context"
                ],

            feedback=
                feedback
        )
    )

    # generation.sql = """
    # SELECT
    #     CustomerName
    # FROM Customer
    # LIMIT 10
    # """


    return {

        "generated_sql":
            generation.sql,

        "sql_explanation":
            generation.explanation,

        "retry_count":
            retry_count,

        "validation_ok":
            False,

        "validation_error":
            "",

        "execution_ok":
            False,

        "execution_error":
            "",

        "trace": [
            f"SQL correction attempt "
            f"{retry_count}",
        ],

        "unit_tests_ok":
            False,

        "unit_test_error":
            "",

        "reflection_ok":
            False,

        "reflection_feedback":
            "",
    }


# =====================================================
# NODE 6
# SQL Execution
# =====================================================

def sql_execution_node(
    state: AgentState
):

    try:

        result = execute_query(
            state[
                "generated_sql"
            ]
        )


        return {

            "execution_ok":
                True,

            "execution_error":
                "",

            "columns":
                result["columns"],

            "rows":
                result["rows"],

            "row_count":
                result["row_count"],

            "trace": [
                f"SQL execution successful. "
                f"{result['row_count']} "
                f"rows returned."
            ]
        }


    except Exception as error:

        return {

            "execution_ok":
                False,

            "execution_error":
                str(error),

            "trace": [
                "SQL execution failed: "
                + str(error)
            ]
        }


# =====================================================
# NODE 7
# Final Response
# =====================================================

def final_response_node(
    state: AgentState
):

    # Unsupported request

    if (
        state.get("intent")
        ==
        "unsupported"
    ):

        final_answer = (
            "This request does not appear "
            "to be a query that can be "
            "answered from the Chinook "
            "database."
        )


    # Successful query

    elif state.get(
        "execution_ok"
    ):

        final_answer = (
            f"Query executed successfully "
            f"and returned "
            f"{state.get('row_count', 0)} "
            f"rows."
        )


    # Validation failure

    elif state.get(
        "validation_error"
    ):

        final_answer = (
            "I could not produce a valid "
            "SQL query after the configured "
            "correction attempts. "
            f"Last validation error: "
            f"{state['validation_error']}"
        )


    # Execution failure

    elif state.get(
        "execution_error"
    ):

        final_answer = (
            "The SQL query could not be "
            "executed successfully. "
            f"Last error: "
            f"{state['execution_error']}"
        )


    else:

        final_answer = (
            "The request could not be "
            "completed."
        )


    return {

        "final_answer":
            final_answer,

        "trace": [
            "Workflow completed"
        ]
    }


# =====================================================
# NODE
# Tool Selection
# =====================================================

def tool_selection_node(
    state: AgentState
):

    selection = select_tools(
        state["question"]
    )

    return {

        "selected_tools":
            selection.tools,

        "tool_selection_reason":
            selection.reason,

        "trace": [
            "Tools selected: "
            + ", ".join(
                selection.tools
            )
        ]
    }

# =====================================================
# NODE
# SQL Unit Testing
# =====================================================

def sql_unit_test_node(
    state: AgentState
):

    result = run_sql_unit_tests(

        question=
            state["question"],

        sql=
            state["generated_sql"]
    )


    print(
        "\n=================================="
    )

    print(
        "SQL UNIT TEST NODE"
    )

    print(
        "=================================="
    )

    print(
        "Generated SQL:"
    )

    print(
        state["generated_sql"]
    )

    print(
        "\nPassed:"
    )

    print(
        result["passed"]
    )

    print(
        "Passed type:"
    )

    print(
        type(
            result["passed"]
        )
    )

    print(
        "\nTest Results:"
    )

    print(
        result["tests"]
    )

    print(
        "\nError:"
    )

    print(
        result["error"]
    )


    if result["passed"]:

        trace_message = (
            "SQL unit tests passed"
        )

    else:

        trace_message = (
            "SQL unit tests failed: "
            + result["error"]
        )


    output = {

        "unit_tests_ok":
            bool(
                result["passed"]
            ),

        "unit_test_results":
            result["tests"],

        "unit_test_error":
            result["error"],

        "trace": [
            trace_message
        ]
    }


    print(
        "\nNODE OUTPUT:"
    )

    print(
        output
    )


    return output

# =====================================================
# NODE
# Self Reflection
# =====================================================

def sql_reflection_node(
    state: AgentState
):

    print(
        "\n=================================="
    )

    print(
        "SQL REFLECTION NODE"
    )

    print(
        "=================================="
    )


    result = (
        reflect_on_sql(

            question=
                state["question"],

            sql=
                state["generated_sql"],

            semantic_context=
                state.get(
                    "semantic_context",
                    {}
                ),

            unit_tests_ok=
                state.get(
                    "unit_tests_ok",
                    False
                ),

            validation_ok=
                state.get(
                    "validation_ok",
                    False
                )
        )
    )


    if result.approved:

        trace_message = (
            (
                "SQL reflection passed "
                f"(score={result.score:.2f})"
            )
        )

    else:

        trace_message = (
            (
                "SQL reflection failed: "
                f"{result.feedback}"
            )
        )


    return {

        "reflection_ok":
            result.approved,

        "reflection_score":
            result.score,

        "reflection_feedback":
            result.feedback,

        "trace": [
            trace_message
        ]
    }