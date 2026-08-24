import json

from graph.client import get_graph
from llm.embeddings import (
    embed_texts
)


def build_concept_texts(
    graph
):
    """
    Build semantic descriptions for
    BusinessConcept nodes.
    """

    result = graph.query(
        """
        MATCH
            (c:BusinessConcept)
            -[:HAS_SYNONYM]->
            (s:Synonym)

        RETURN
            c.id,
            c.name,
            c.description,
            collect(s.name)
        """
    )

    records = []

    for row in result.result_set:

        concept_id = row[0]
        name = row[1]
        description = row[2]
        synonyms = row[3]

        semantic_text = (
            f"Business concept: {name}. "
            f"Description: {description}. "
            f"Alternative words: "
            f"{', '.join(synonyms)}."
        )

        records.append(
            {
                "id": concept_id,
                "semantic_text":
                    semantic_text
            }
        )

    return records


def build_metric_texts(
    graph
):
    """
    Build semantic descriptions for Metric nodes.
    """

    result = graph.query(
        """
        MATCH
            (m:Metric)
            -[:HAS_SYNONYM]->
            (s:Synonym)

        RETURN
            m.id,
            m.name,
            m.description,
            m.expression,
            collect(s.name)
        """
    )

    records = []

    for row in result.result_set:

        metric_id = row[0]
        name = row[1]
        description = row[2]
        expression = row[3]
        synonyms = row[4]

        semantic_text = (
            f"Business metric: {name}. "
            f"Description: {description}. "
            f"Formula: {expression}. "
            f"Alternative words: "
            f"{', '.join(synonyms)}."
        )

        records.append(
            {
                "id": metric_id,
                "semantic_text":
                    semantic_text
            }
        )

    return records


def store_embeddings(
    graph,
    label,
    records
):
    """
    Generate embeddings in one batch and
    store them in FalkorDB.
    """

    if not records:
        return None

    texts = [
        record["semantic_text"]
        for record in records
    ]

    print(
        f"Generating embeddings for "
        f"{len(texts)} {label} nodes..."
    )

    vectors = embed_texts(
        texts
    )

    dimension = len(
        vectors[0]
    )

    for record, vector in zip(
        records,
        vectors
    ):

        # Convert Python vector into a valid
        # Cypher array literal.
        vector_literal = json.dumps(
            [
                float(value)
                for value in vector
            ]
        )

        query = f"""
        MATCH
            (n:{label} {{
                id: $id
            }})

        SET
            n.semantic_text =
                $semantic_text,

            n.embedding =
                vecf32(
                    {vector_literal}
                )
        """

        graph.query(
            query,
            {
                "id":
                    record["id"],

                "semantic_text":
                    record[
                        "semantic_text"
                    ]
            }
        )

    return dimension


def recreate_vector_index(
    graph,
    label,
    dimension
):
    """
    Recreate vector index so this script
    can safely be rerun.
    """

    try:

        graph.query(
            f"""
            DROP VECTOR INDEX
            FOR (n:{label})
            ON (n.embedding)
            """
        )

    except Exception:
        pass


    graph.query(
        f"""
        CREATE VECTOR INDEX
        FOR (n:{label})
        ON (n.embedding)

        OPTIONS {{
            dimension: {dimension},
            similarityFunction: 'cosine'
        }}
        """
    )

    print(
        f"Vector index created: "
        f"{label}.embedding"
    )


def build_semantic_embeddings():

    graph = get_graph()

    print(
        "\nBuilding semantic embeddings..."
    )


    # ---------------------------------
    # Business concepts
    # ---------------------------------

    concepts = (
        build_concept_texts(
            graph
        )
    )

    concept_dimension = (
        store_embeddings(
            graph,
            "BusinessConcept",
            concepts
        )
    )

    if concept_dimension:

        recreate_vector_index(
            graph,
            "BusinessConcept",
            concept_dimension
        )


    # ---------------------------------
    # Metrics
    # ---------------------------------

    metrics = (
        build_metric_texts(
            graph
        )
    )

    metric_dimension = (
        store_embeddings(
            graph,
            "Metric",
            metrics
        )
    )

    if metric_dimension:

        recreate_vector_index(
            graph,
            "Metric",
            metric_dimension
        )


    print(
        "\nSemantic embeddings created."
    )


if __name__ == "__main__":

    build_semantic_embeddings()