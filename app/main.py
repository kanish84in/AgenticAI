from fastapi import (
    FastAPI,
    HTTPException,
    Request
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.templating import (
    Jinja2Templates
)

from pydantic import BaseModel


from workflow.graph import (
    text2sql_agent
)

app = FastAPI(
    title="Agentic AI Text-to-SQL"
)


templates = Jinja2Templates(
    directory="app/templates"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class QueryRequest(BaseModel):
    question: str


@app.get("/")
async def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }



@app.post("/query")
def query(
    payload: QueryRequest
):

    try:

        initial_state = {

            "question":
                payload.question,

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
                    "recursion_limit":
                        20
                }
            )
        )

        print(
            "\n\n========================================"
        )
        print(
            "FINAL LANGGRAPH STATE"
        )
        print(
            "========================================"
        )

        from pprint import pprint

        pprint(result)

        print(
            "========================================\n"
        )



        semantic_context = (
            result.get(
                "semantic_context",
                {}
            )
        )


        return {

            "question":
                payload.question,

            "intent":
                result.get(
                    "intent",
                    ""
                ),

            "plan":
                result.get(
                    "plan",
                    []
                ),

            "retrieval_mode":
                result.get(
                    "retrieval_mode",
                    ""
                ),

            "concepts":
                semantic_context.get(
                    "concepts",
                    []
                ),

            "metrics":
                semantic_context.get(
                    "metrics",
                    []
                ),

            "tables":
                semantic_context.get(
                    "tables",
                    []
                ),

            "join_paths":
                semantic_context.get(
                    "join_paths",
                    []
                ),

            "joins":
                semantic_context.get(
                    "joins",
                    []
                ),

            # ======================================
            # Tool selection
            # ======================================

            "selected_tools":
                result.get(
                    "selected_tools",
                    []
                ),

            "tool_selection_reason":
                result.get(
                    "tool_selection_reason",
                    ""
                ),

            # ======================================
            # SQL
            # ======================================

            "generated_sql":
                result.get(
                    "generated_sql",
                    ""
                ),

            "explanation":
                result.get(
                    "sql_explanation",
                    ""
                ),

            # ======================================
            # Unit tests
            # ======================================

            "unit_tests_ok":
                result.get(
                    "unit_tests_ok",
                    False
                ),

            "unit_test_results":
                result.get(
                    "unit_test_results",
                    []
                ),

            "unit_test_error":
                result.get(
                    "unit_test_error",
                    ""
                ),

            # ======================================
            # Validation
            # ======================================

            "validation_ok":
                result.get(
                    "validation_ok",
                    False
                ),

            "validation_error":
                result.get(
                    "validation_error",
                    ""
                ),

            # ======================================
            # Reflection
            # ======================================

            "reflection_ok":
                result.get(
                    "reflection_ok",
                    False
                ),

            "reflection_score":
                result.get(
                    "reflection_score",
                    0.0
                ),

            "reflection_feedback":
                result.get(
                    "reflection_feedback",
                    ""
                ),

            # ======================================
            # Execution
            # ======================================

            "execution_ok":
                result.get(
                    "execution_ok",
                    False
                ),

            "execution_error":
                result.get(
                    "execution_error",
                    ""
                ),

            "columns":
                result.get(
                    "columns",
                    []
                ),

            "rows":
                result.get(
                    "rows",
                    []
                ),

            "row_count":
                result.get(
                    "row_count",
                    0
                ),

            # ======================================
            # Workflow
            # ======================================

            "retry_count":
                result.get(
                    "retry_count",
                    0
                ),

            "final_answer":
                result.get(
                    "final_answer",
                    ""
                ),

            "trace":
                result.get(
                    "trace",
                    []
                )
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

