from typing import Literal

from pydantic import (
    BaseModel,
    Field
)


# =====================================================
# Tool Types
# =====================================================

RetrievalTool = Literal[
    "semantic_search",
    "graph_search",
    "schema_search"
]


# =====================================================
# Structured Output
# =====================================================

class ToolSelection(BaseModel):

    tools: list[
        RetrievalTool
    ] = Field(
        min_length=1
    )

    reason: str


# =====================================================
# Schema-related keywords
# =====================================================

SCHEMA_KEYWORDS = {

    "schema",

    "table",
    "tables",

    "column",
    "columns",

    "primary key",
    "foreign key",

    "metadata",

    "database structure",

    "relationships",

    "describe table",

    "show schema"
}


# =====================================================
# Schema Intent Detection
# =====================================================

def has_schema_intent(
    question: str
) -> bool:

    question_lower = (
        question
        .lower()
        .strip()
    )


    return any(

        keyword
        in
        question_lower

        for keyword
        in SCHEMA_KEYWORDS
    )


# =====================================================
# Tool Selection
# =====================================================

def select_tools(
    question: str
) -> ToolSelection:

    # -------------------------------------------------
    # Normal analytical Text-to-SQL question
    # -------------------------------------------------

    tools = [
        "semantic_search",
        "graph_search"
    ]


    # -------------------------------------------------
    # Explicit schema / metadata request
    # -------------------------------------------------

    if has_schema_intent(
        question
    ):

        tools.append(
            "schema_search"
        )


        reason = (
            "Semantic, graph and schema "
            "retrieval are required."
        )


    else:

        reason = (
            "Semantic concepts and graph "
            "relationships are required."
        )


    selection = ToolSelection(

        tools=tools,

        reason=reason
    )


    print(
        "\nDETERMINISTIC TOOL SELECTION:"
    )

    print(
        selection
    )


    return selection