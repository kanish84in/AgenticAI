from typing import Literal

from langgraph.graph import (
    END,
    START,
    StateGraph
)

from workflow.state import (
    AgentState
)

from workflow.nodes import (
    final_response_node,
    intent_planner_node,
    semantic_retrieval_node,
    sql_correction_node,
    sql_execution_node,
    sql_generation_node,
    sql_reflection_node,
    sql_unit_test_node,
    sql_validation_node,
    tool_selection_node
)


# =====================================================
# ROUTER 1
# After Intent
# =====================================================

def route_after_intent(
    state: AgentState
) -> Literal[
    "tool_selection",
    "final_response"
]:

    if (
        state.get("intent")
        ==
        "data_query"
    ):
        return "tool_selection"

    return "final_response"

# =====================================================
# ROUTER 2
# After Validation
# =====================================================

def route_after_validation(
    state: AgentState
) -> Literal[
    "sql_reflection",
    "sql_correction",
    "final_response"
]:

    if state.get(
        "validation_ok",
        False
    ):

        return "sql_reflection"


    retry_count = state.get(
        "retry_count",
        0
    )

    max_retries = state.get(
        "max_retries",
        2
    )


    if retry_count < max_retries:

        return "sql_correction"


    return "final_response"

# =====================================================
# ROUTER 3
# After Execution
# =====================================================

def route_after_execution(
    state: AgentState
) -> Literal[
    "final_response",
    "sql_correction"
]:

    if state.get(
        "execution_ok"
    ):

        return (
            "final_response"
        )


    retry_count = (
        state.get(
            "retry_count",
            0
        )
    )

    max_retries = (
        state.get(
            "max_retries",
            2
        )
    )


    if (
        retry_count
        <
        max_retries
    ):

        return (
            "sql_correction"
        )


    return (
        "final_response"
    )


# ===========================================
# Create unit-test routing
# ============================================

def route_after_unit_tests(
    state: AgentState
):

    unit_tests_ok = state.get(
        "unit_tests_ok",
        False
    )

    print(
        "\n=================================="
    )

    print(
        "ROUTING AFTER UNIT TESTS"
    )

    print(
        "=================================="
    )

    print(
        "unit_tests_ok:",
        unit_tests_ok
    )

    print(
        "unit_tests_ok type:",
        type(unit_tests_ok)
    )

    print(
        "retry_count:",
        state.get(
            "retry_count",
            0
        )
    )

    print(
        "max_retries:",
        state.get(
            "max_retries",
            2
        )
    )


    if unit_tests_ok:

        print(
            ">>> Routing to SQL VALIDATION"
        )

        return "sql_validation"


    retry_count = state.get(
        "retry_count",
        0
    )

    max_retries = state.get(
        "max_retries",
        2
    )


    if retry_count < max_retries:

        print(
            ">>> Routing to SQL CORRECTION"
        )

        return "sql_correction"


    print(
        ">>> Retry limit reached. "
        "Routing to FINAL RESPONSE"
    )

    return "final_response"

# ===================================================
# Route after reflection
# ===================================================
def route_after_reflection(
    state: AgentState
):

    if state.get(
        "reflection_ok"
    ):

        return (
            "sql_execution"
        )


    retry_count = state.get(
        "retry_count",
        0
    )

    max_retries = state.get(
        "max_retries",
        2
    )


    if retry_count < max_retries:

        return (
            "sql_correction"
        )


    return (
        "final_response"
    )


# =====================================================
# BUILD LANGGRAPH
# =====================================================

builder = StateGraph(
    AgentState
)


# -----------------------------
# Nodes
# -----------------------------

builder.add_node(
    "intent_planner",
    intent_planner_node
)

builder.add_node(
    "semantic_retrieval",
    semantic_retrieval_node
)

builder.add_node(
    "sql_generation",
    sql_generation_node
)

builder.add_node(
    "sql_validation",
    sql_validation_node
)

builder.add_node(
    "sql_correction",
    sql_correction_node
)

builder.add_node(
    "sql_execution",
    sql_execution_node
)

builder.add_node(
    "final_response",
    final_response_node
)

builder.add_node(
    "tool_selection",
    tool_selection_node
)

builder.add_node(
    "sql_unit_test",
    sql_unit_test_node
)

builder.add_node(
    "sql_reflection",
    sql_reflection_node
)

# -----------------------------
# Start
# -----------------------------

builder.add_edge(
    START,
    "intent_planner"
)


# -----------------------------
# Intent routing
# -----------------------------

builder.add_conditional_edges(
    "intent_planner",
    route_after_intent,
    {
        "tool_selection":
            "tool_selection",

        "final_response":
            "final_response"
    }
)

builder.add_edge(
    "tool_selection",
    "semantic_retrieval"
)

# -----------------------------
# Retrieval → generation
# -----------------------------

builder.add_edge(
    "semantic_retrieval",
    "sql_generation"
)


# -----------------------------
# Generation → Unit test
# -----------------------------

builder.add_edge(
    "sql_generation",
    "sql_unit_test"
)

builder.add_conditional_edges(

    "sql_unit_test",

    route_after_unit_tests,

    {
        "sql_validation":
            "sql_validation",

        "sql_correction":
            "sql_correction",

        "final_response":
            "final_response"
    }
)


# -----------------------------
# Validation routing
# -----------------------------

builder.add_conditional_edges(

    "sql_validation",

    route_after_validation,

    {
        "sql_reflection":
            "sql_reflection",

        "sql_correction":
            "sql_correction",

        "final_response":
            "final_response"
    }
)


# -----------------------------
# Correction → validation
# -----------------------------

builder.add_edge(
    "sql_correction",
    "sql_unit_test"
)


# -----------------------------
# Execution routing
# -----------------------------

builder.add_conditional_edges(

    "sql_execution",

    route_after_execution,

    {
        "final_response":
            "final_response",

        "sql_correction":
            "sql_correction"
    }
)

builder.add_conditional_edges(

    "sql_reflection",

    route_after_reflection,

    {
        "sql_execution":
            "sql_execution",

        "sql_correction":
            "sql_correction",

        "final_response":
            "final_response"
    }
)

# -----------------------------
# End
# -----------------------------

builder.add_edge(
    "final_response",
    END
)


# =====================================================
# Compile
# =====================================================

text2sql_agent = (
    builder.compile()
)