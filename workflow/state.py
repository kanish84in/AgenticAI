import operator

from typing import (
    Annotated,
    Any,
    TypedDict
)


class AgentState(
    TypedDict,
    total=False
):

    # =====================================
    # User Input
    # =====================================

    question: str


    # =====================================
    # Intent / Planning
    # =====================================

    intent: str

    plan: list[str]


    # =====================================
    # Tool Selection
    # =====================================

    selected_tools: list[str]

    tool_selection_reason: str


    # =====================================
    # Semantic Retrieval
    # =====================================

    retrieval_mode: str

    semantic_context: dict[str, Any]

    schema_context: str


    # =====================================
    # SQL Generation
    # =====================================

    generated_sql: str

    sql_explanation: str


    # =====================================
    # SQL Unit Testing
    # =====================================

    unit_tests_ok: bool

    unit_test_results: list[
        dict[str, Any]
    ]

    unit_test_error: str


    # =====================================
    # SQL Validation
    # =====================================

    validation_ok: bool

    validation_error: str


    # =====================================
    # Self Reflection
    # =====================================

    reflection_ok: bool

    reflection_feedback: str

    reflection_score: float


    # =====================================
    # SQL Execution
    # =====================================

    execution_ok: bool

    execution_error: str

    columns: list[str]

    rows: list[
        dict[str, Any]
    ]

    row_count: int


    # =====================================
    # Retry Management
    # =====================================

    retry_count: int

    max_retries: int


    # =====================================
    # Final Response
    # =====================================

    final_answer: str


    # =====================================
    # Agent Trace
    # =====================================

    trace: Annotated[
        list[str],
        operator.add
    ]