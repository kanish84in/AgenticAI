import json

from graph.client import get_graph
from llm.embeddings import embed_text

from app.config import (
    VECTOR_TOP_K
)


def vector_literal(
    vector
):
    """
    Convert vector to Cypher list.
    """

    return json.dumps(
        [
            float(value)
            for value in vector
        ]
    )


def search_business_concepts(
    question: str,
    top_k: int = None
):

    if top_k is None:
        top_k = VECTOR_TOP_K

    graph = get_graph()

    embedding = embed_text(
        question
    )

    query_vector = (
        vector_literal(
            embedding
        )
    )


    query = f"""
    CALL
        db.idx.vector.queryNodes(
            'BusinessConcept',
            'embedding',
            {top_k},
            vecf32(
                {query_vector}
            )
        )

    YIELD
        node,
        score

    RETURN
        node.id,
        node.name,
        node.description,
        node.semantic_text,
        score

    ORDER BY
        score DESC
    """


    result = graph.query(
        query
    )


    concepts = []

    for row in result.result_set:

        concepts.append(
            {
                "id":
                    row[0],

                "name":
                    row[1],

                "description":
                    row[2],

                "semantic_text":
                    row[3],

                "similarity_score":
                    float(row[4])
            }
        )

    return concepts


def search_metrics(
    question: str,
    top_k: int = None
):

    if top_k is None:
        top_k = VECTOR_TOP_K

    graph = get_graph()

    embedding = embed_text(
        question
    )

    query_vector = (
        vector_literal(
            embedding
        )
    )


    query = f"""
    CALL
        db.idx.vector.queryNodes(
            'Metric',
            'embedding',
            {top_k},
            vecf32(
                {query_vector}
            )
        )

    YIELD
        node,
        score

    RETURN
        node.id,
        node.name,
        node.description,
        node.expression,
        node.semantic_text,
        score

    ORDER BY
        score DESC
    """


    result = graph.query(
        query
    )


    metrics = []

    for row in result.result_set:

        metrics.append(
            {
                "id":
                    row[0],

                "name":
                    row[1],

                "description":
                    row[2],

                "expression":
                    row[3],

                "semantic_text":
                    row[4],

                "similarity_score":
                    float(row[5])
            }
        )

    return metrics