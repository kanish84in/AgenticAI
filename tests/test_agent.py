from pprint import pprint

from workflow.graph import (
    text2sql_agent
)


question = (
    "Show top 5 listeners by income"
)


initial_state = {

    "question":
        question,

    "retry_count":
        0,

    "max_retries":
        2,

    "trace":
        []
}


result = (
    text2sql_agent.invoke(
        initial_state,

        config={
            "recursion_limit": 20
        }
    )
)


print(
    "\n"
    + "=" * 70
)

print(
    "QUESTION"
)

print(
    result["question"]
)


print(
    "\nPLAN"
)

pprint(
    result.get(
        "plan"
    )
)


print(
    "\nSELECTED TABLES"
)

pprint(
    result
    .get(
        "semantic_context",
        {}
    )
    .get(
        "tables",
        []
    )
)


print(
    "\nGENERATED SQL"
)

print(
    result.get(
        "generated_sql"
    )
)


print(
    "\nVALIDATION"
)

print(
    result.get(
        "validation_ok"
    )
)


print(
    "\nEXECUTION"
)

print(
    result.get(
        "execution_ok"
    )
)


print(
    "\nRESULTS"
)

pprint(
    result.get(
        "rows"
    )
)


print(
    "\nAGENT TRACE"
)

for step in result.get(
    "trace",
    []
):

    print(
        "✓",
        step
    )

print(
    "\nSELECTED TOOLS"
)

pprint(
    result.get(
        "selected_tools",
        []
    )
)


print(
    "\nSQL UNIT TESTS"
)

pprint(
    result.get(
        "unit_test_results",
        []
    )
)


print(
    "\nSELF REFLECTION"
)

print(
    "Approved:",
    result.get(
        "reflection_ok"
    )
)

print(
    "Score:",
    result.get(
        "reflection_score"
    )
)

print(
    "Feedback:",
    result.get(
        "reflection_feedback"
    )
)