from typing import Literal

from ollama import Client

from pydantic import (
    BaseModel,
    Field
)

from app.config import (
    OLLAMA_HOST,
    OLLAMA_MODEL
)


client = Client(
    host=OLLAMA_HOST
)


class IntentPlan(BaseModel):

    intent: Literal[
        "data_query",
        "unsupported"
    ]

    plan: list[str] = Field(
        default_factory=list
    )

    note: str = ""


SYSTEM_PROMPT = """
You classify requests for a Text-to-SQL system.

The application contains the Chinook music
database.

Classify the request as:

data_query
- The user wants information that can
  reasonably be answered from the database.

unsupported
- The request is unrelated to querying or
  analyzing the database.

For a data_query, also produce a short execution
plan.

The plan must describe actions, not internal
reasoning.

Example plan:

[
    "Identify relevant business concepts",
    "Retrieve relevant tables and joins",
    "Generate SQLite query",
    "Validate query",
    "Execute query"
]
"""


def classify_and_plan(
    question: str
) -> IntentPlan:

    response = client.chat(

        model=OLLAMA_MODEL,

        messages=[
            {
                "role":
                    "system",

                "content":
                    SYSTEM_PROMPT
            },

            {
                "role":
                    "user",

                "content":
                    question
            }
        ],

        format=
            IntentPlan.model_json_schema(),

        think=False,

        keep_alive="30m",

        options={
            "temperature": 0,
            "num_predict": 200
        }
    )


    return (
        IntentPlan
        .model_validate_json(
            response.message.content
        )
    )