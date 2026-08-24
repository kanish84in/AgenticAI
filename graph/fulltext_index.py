from graph.client import (
    get_graph
)


# =====================================================
# Drop Existing Full-Text Index
# =====================================================

def drop_fulltext_index(
    graph,
    label: str
):
    """
    Drop an existing FalkorDB full-text index.

    It is safe if the index does not already exist.
    """

    try:

        graph.query(
            f"""
            CALL db.idx.fulltext.drop(
                '{label}'
            )
            """
        )

        print(
            f"Dropped existing full-text "
            f"index for {label}."
        )

    except Exception as error:

        print(
            f"No existing full-text index "
            f"for {label}."
        )

        print(
            f"Details: {error}"
        )


# =====================================================
# Create BusinessConcept Full-Text Index
# =====================================================

def create_business_concept_index(
    graph
):
    """
    Create full-text search index for
    BusinessConcept nodes.
    """

    print(
        "\nCreating BusinessConcept "
        "full-text index..."
    )


    graph.query(
        """
        CALL db.idx.fulltext.createNodeIndex(
            'BusinessConcept',
            'name',
            'description',
            'semantic_text'
        )
        """
    )


    print(
        "BusinessConcept full-text "
        "index created."
    )


# =====================================================
# Create Metric Full-Text Index
# =====================================================

def create_metric_index(
    graph
):
    """
    Create full-text search index for Metric nodes.
    """

    print(
        "\nCreating Metric "
        "full-text index..."
    )


    graph.query(
        """
        CALL db.idx.fulltext.createNodeIndex(
            'Metric',
            'name',
            'description',
            'semantic_text'
        )
        """
    )


    print(
        "Metric full-text "
        "index created."
    )


# =====================================================
# Recreate Full-Text Indexes
# =====================================================

def create_fulltext_indexes():

    print(
        "\n=================================="
    )

    print(
        "BUILDING FALKORDB FULL-TEXT INDEXES"
    )

    print(
        "=================================="
    )


    graph = get_graph()


    # =================================================
    # BusinessConcept
    # =================================================

    drop_fulltext_index(
        graph,
        "BusinessConcept"
    )


    create_business_concept_index(
        graph
    )


    # =================================================
    # Metric
    # =================================================

    drop_fulltext_index(
        graph,
        "Metric"
    )


    create_metric_index(
        graph
    )


    print(
        "\n=================================="
    )

    print(
        "FULL-TEXT INDEXES CREATED"
    )

    print(
        "=================================="
    )


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    create_fulltext_indexes()