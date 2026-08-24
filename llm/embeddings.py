from ollama import Client

from app.config import (
    OLLAMA_HOST,
    EMBEDDING_MODEL
)


client = Client(
    host=OLLAMA_HOST
)


def embed_text(
    text: str
):
    """
    Generate one embedding vector.
    """

    response = client.embed(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response[
        "embeddings"
    ][0]


def embed_texts(
    texts: list[str]
):
    """
    Generate embeddings in a batch.
    """

    if not texts:
        return []

    response = client.embed(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return response[
        "embeddings"
    ]


def get_embedding_dimension():
    """
    Determine dimension dynamically instead
    of hardcoding it.
    """

    vector = embed_text(
        "dimension test"
    )

    return len(vector)