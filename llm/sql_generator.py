import re
import time

from typing import Optional

from ollama import Client

from pydantic import (
    BaseModel,
    field_validator
)

from app.config import (
    OLLAMA_HOST,
    OLLAMA_SQL_MODEL
)


# =====================================================
# Ollama Client
#
# We do not impose a client-side timeout because
# local inference can be slow.
# =====================================================

client = Client(
    host=OLLAMA_HOST,
    timeout=None
)


# =====================================================
# Public SQL Generation Result
#
# Keep this interface because workflow/nodes.py
# already expects:
#
# result.sql
# result.explanation
# =====================================================

class SQLGeneration(BaseModel):

    sql: str

    explanation: str


    # =================================================
    # Final SQL safety / completeness validation
    # =================================================

    @field_validator(
        "sql"
    )
    @classmethod
    def validate_sql(
        cls,
        value: str
    ) -> str:

        if value is None:

            raise ValueError(
                "Generated SQL cannot be null."
            )


        sql = (
            value.strip()
        )


        if not sql:

            raise ValueError(
                "Generated SQL cannot be empty."
            )


        sql_lower = (
            sql.lower()
        )


        # ---------------------------------------------
        # Placeholder detection
        # ---------------------------------------------

        invalid_patterns = [

            "...",

            "…",

            "<sql>",

            "<query>",

            "sql here",

            "query here",

            "your sql"
        ]


        for pattern in invalid_patterns:

            if (
                pattern
                in
                sql_lower
            ):

                raise ValueError(
                    (
                        "Generated SQL contains "
                        "placeholder or incomplete "
                        "content."
                    )
                )


        # ---------------------------------------------
        # SELECT / WITH only
        # ---------------------------------------------

        if not re.match(
            r"^\s*(SELECT|WITH)\b",
            sql,
            flags=re.IGNORECASE
        ):

            raise ValueError(
                (
                    "Generated SQL must begin "
                    "with SELECT or WITH."
                )
            )


        # ---------------------------------------------
        # Protect against write operations
        # ---------------------------------------------

        blocked_operations = [

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


        for operation in blocked_operations:

            if re.search(
                (
                    r"\b"
                    +
                    re.escape(
                        operation
                    )
                    +
                    r"\b"
                ),
                sql,
                flags=re.IGNORECASE
            ):

                raise ValueError(
                    (
                        "Generated SQL contains "
                        f"prohibited operation: "
                        f"{operation}."
                    )
                )


        # ---------------------------------------------
        # Basic completeness check
        # ---------------------------------------------

        if len(
            sql.split()
        ) < 6:

            raise ValueError(
                (
                    "Generated SQL appears "
                    "to be incomplete."
                )
            )


        return sql


# =====================================================
# SQL Generator Prompt
#
# Keep this concise.
#
# qwen2.5-coder is already code focused, so we do not
# need a large reasoning-heavy prompt.
# =====================================================

SQL_SYSTEM_PROMPT = """
You are an expert SQLite database engineer.

Generate one complete executable SQLite query that
answers the user's question.

Rules:

1. Use only tables and columns provided in the context.

2. Use only join relationships provided in the context.

3. Business metric definitions provided in the context
   are authoritative.

4. If a requested metric has an authoritative formula,
   use that formula exactly.

5. For a top-N request:
   - calculate the requested metric
   - sort by that metric in the required direction
   - apply LIMIT N

6. When aggregation is used, include every selected
   non-aggregated column in GROUP BY.

7. Use explicit JOIN syntax.

8. Generate SELECT or WITH queries only.

9. Write the complete executable SQL query.

10. Return only SQL.
"""


# =====================================================
# Clean Model Output
#
# qwen2.5-coder may correctly generate:
#
# ```sql
# SELECT ...
# ```
#
# We normalize that into plain executable SQL.
# =====================================================

def clean_sql_output(
    raw_output: str
) -> str:

    if not raw_output:

        return ""


    cleaned = (
        raw_output.strip()
    )


    # =================================================
    # Remove opening markdown SQL fence
    # =================================================

    cleaned = re.sub(
        r"^\s*```(?:sql|sqlite)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )


    # =================================================
    # Remove closing markdown fence
    # =================================================

    cleaned = re.sub(
        r"\s*```\s*$",
        "",
        cleaned
    )


    cleaned = (
        cleaned.strip()
    )


    # =================================================
    # Occasionally a model may prefix SQL with:
    #
    # SQL:
    # Query:
    #
    # Remove those safely.
    # =================================================

    cleaned = re.sub(
        r"^\s*(SQL|QUERY)\s*:\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )


    return (
        cleaned.strip()
    )


# =====================================================
# Extract Ollama Response Content
# =====================================================

def extract_response_content(
    response
) -> str:

    try:

        return (
            response
            .message
            .content
        )


    except Exception:

        pass


    try:

        return (
            response[
                "message"
            ][
                "content"
            ]
        )


    except Exception as error:

        raise RuntimeError(
            (
                "Unable to extract SQL content "
                "from Ollama response."
            )
        ) from error


# =====================================================
# Response Value Helper
# =====================================================

def get_response_value(
    response,
    name: str,
    default=None
):

    value = getattr(
        response,
        name,
        None
    )


    if (
        value is not None
    ):

        return value


    try:

        return response.get(
            name,
            default
        )

    except Exception:

        return default


# =====================================================
# Performance Logging
# =====================================================

def print_ollama_metrics(
    response,
    elapsed_time: float
):

    prompt_tokens = (
        get_response_value(
            response,
            "prompt_eval_count",
            0
        )
        or
        0
    )


    generated_tokens = (
        get_response_value(
            response,
            "eval_count",
            0
        )
        or
        0
    )


    load_duration = (
        get_response_value(
            response,
            "load_duration",
            0
        )
        or
        0
    )


    prompt_duration = (
        get_response_value(
            response,
            "prompt_eval_duration",
            0
        )
        or
        0
    )


    generation_duration = (
        get_response_value(
            response,
            "eval_duration",
            0
        )
        or
        0
    )


    # Ollama durations are nanoseconds.

    load_seconds = (
        load_duration
        /
        1_000_000_000
    )


    prompt_seconds = (
        prompt_duration
        /
        1_000_000_000
    )


    generation_seconds = (
        generation_duration
        /
        1_000_000_000
    )


    print(
        (
            f"\nSQL model response time: "
            f"{elapsed_time:.2f} seconds"
        ),
        flush=True
    )


    print(
        (
            f"SQL model: "
            f"{OLLAMA_SQL_MODEL}"
        ),
        flush=True
    )


    print(
        (
            f"Prompt tokens: "
            f"{prompt_tokens}"
        ),
        flush=True
    )


    print(
        (
            f"Generated tokens: "
            f"{generated_tokens}"
        ),
        flush=True
    )


    print(
        (
            f"Model load time: "
            f"{load_seconds:.2f} seconds"
        ),
        flush=True
    )


    if (
        prompt_seconds
        >
        0
    ):

        prompt_speed = (
            prompt_tokens
            /
            prompt_seconds
        )


        print(
            (
                f"Prompt processing speed: "
                f"{prompt_speed:.2f} tokens/sec"
            ),
            flush=True
        )


    if (
        generation_seconds
        >
        0
    ):

        generation_speed = (
            generated_tokens
            /
            generation_seconds
        )


        print(
            (
                f"Generation speed: "
                f"{generation_speed:.2f} tokens/sec"
            ),
            flush=True
        )


# =====================================================
# Sanitize LangGraph Correction Feedback
#
# Important:
# Do not pass a previous malformed SQL query back into
# the LLM. Send only the actionable failure reason.
# =====================================================

def sanitize_feedback(
    feedback: Optional[str]
) -> Optional[str]:

    if not feedback:

        return None


    feedback_lower = (
        feedback.lower()
    )


    instructions = []


    # =================================================
    # LIMIT
    # =================================================

    if (
        "limit"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Include the exact LIMIT requested "
                "by the user's top-N question."
            )
        )


    # =================================================
    # Syntax
    # =================================================

    if (
        "syntax"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Reconstruct the complete query "
                "using valid SQLite syntax."
            )
        )


    # =================================================
    # Missing column
    # =================================================

    if (
        "no such column"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Use only columns explicitly listed "
                "in the database context."
            )
        )


    # =================================================
    # Missing table
    # =================================================

    if (
        "no such table"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Use only tables explicitly listed "
                "in the database context."
            )
        )


    # =================================================
    # GROUP BY
    # =================================================

    if (
        "group"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Include every selected "
                "non-aggregated column in GROUP BY."
            )
        )


    # =================================================
    # Placeholder / incomplete
    # =================================================

    if (
        "placeholder"
        in
        feedback_lower
        or
        "incomplete"
        in
        feedback_lower
    ):

        instructions.append(
            (
                "Generate the entire executable SQL "
                "query from beginning to end."
            )
        )


    # =================================================
    # Fallback
    # =================================================

    if not instructions:

        instructions.append(
            (
                "The previous query failed testing. "
                "Generate a corrected complete query "
                "from the supplied context."
            )
        )


    return "\n".join(
        instructions
    )


# =====================================================
# Build User Prompt
# =====================================================

def build_user_prompt(
    question: str,
    schema: str,
    feedback: Optional[str] = None,
    retry: bool = False
) -> str:

    prompt = f"""
QUESTION
========
{question}


DATABASE AND BUSINESS CONTEXT
=============================
{schema}


TASK
====
Generate the complete executable SQLite query needed
to answer the question.
"""


    # =================================================
    # LangGraph correction
    # =================================================

    sanitized_feedback = (
        sanitize_feedback(
            feedback
        )
    )


    if sanitized_feedback:

        prompt += f"""


CORRECTION REQUIREMENTS
=======================
{sanitized_feedback}
"""


    # =================================================
    # Internal retry
    # =================================================

    if retry:

        prompt += """


RETRY
=====
The previous model response could not be accepted.

Reconstruct the complete query using only the
question and database context above.
"""


    return prompt


# =====================================================
# Deterministic Explanation
#
# We do not spend another LLM call generating a simple
# explanation.
# =====================================================

def create_explanation(
    question: str
) -> str:

    cleaned_question = (
        question.strip()
    )


    if cleaned_question.endswith(
        "?"
    ):

        cleaned_question = (
            cleaned_question[:-1]
        )


    return (
        "Generated SQLite query for: "
        f"{cleaned_question}."
    )


# =====================================================
# Generate SQL
# =====================================================

def generate_sql(
    question: str,
    schema: str,
    feedback: Optional[str] = None
) -> SQLGeneration:

    max_attempts = (
        2
    )


    last_error = (
        None
    )


    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            (
                f"\nSQL generation attempt "
                f"{attempt}/{max_attempts}"
            ),
            flush=True
        )


        retry = (
            attempt
            >
            1
        )


        user_prompt = (
            build_user_prompt(

                question=
                    question,

                schema=
                    schema,

                feedback=
                    feedback,

                retry=
                    retry
            )
        )


        start_time = (
            time.time()
        )


        try:

            # =================================================
            # Raw SQL generation
            #
            # No JSON schema.
            # No structured-output mode.
            #
            # qwen2.5-coder directly generates SQL.
            # =================================================

            response = (
                client.chat(

                    model=
                        OLLAMA_SQL_MODEL,

                    messages=[

                        {
                            "role":
                                "system",

                            "content":
                                SQL_SYSTEM_PROMPT
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


            print_ollama_metrics(
                response,
                elapsed_time
            )


            raw_output = (
                extract_response_content(
                    response
                )
            )


            print(
                "\nRAW SQL GENERATOR OUTPUT:",
                flush=True
            )


            print(
                raw_output,
                flush=True
            )


            # =================================================
            # Remove markdown / formatting
            # =================================================

            cleaned_sql = (
                clean_sql_output(
                    raw_output
                )
            )


            print(
                "\nCLEANED SQL:",
                flush=True
            )


            print(
                cleaned_sql,
                flush=True
            )


            # =================================================
            # Validate using our public Pydantic model
            # =================================================

            result = (
                SQLGeneration(

                    sql=
                        cleaned_sql,

                    explanation=
                        create_explanation(
                            question
                        )
                )
            )


            print(
                (
                    "\nSQL output validated "
                    "successfully."
                ),
                flush=True
            )


            return result


        except Exception as error:

            last_error = (
                error
            )


            print(
                "\nSQL GENERATION ATTEMPT FAILED:",
                flush=True
            )


            print(
                str(
                    error
                ),
                flush=True
            )


            if (
                attempt
                <
                max_attempts
            ):

                print(
                    (
                        "\nRetrying SQL generation "
                        "from the clean context..."
                    ),
                    flush=True
                )


                continue


    # =================================================
    # All internal retries failed
    # =================================================

    raise RuntimeError(
        (
            "SQL generation failed after "
            f"{max_attempts} attempts. "
            f"Last error: {last_error}"
        )
    )