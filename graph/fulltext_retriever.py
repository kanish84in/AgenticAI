import re

from graph.client import (
    get_graph
)


# =====================================================
# Stop words
# =====================================================

STOP_WORDS = {
    "show",
    "give",
    "get",
    "find",
    "display",
    "list",
    "which",
    "what",
    "who",
    "where",
    "how",
    "the",
    "a",
    "an",
    "by",
    "of",
    "for",
    "from",
    "in",
    "on",
    "to",
    "with",
    "most",
    "top",
    "me"
}


# =====================================================
# Build FalkorDB full-text search query
# =====================================================

def build_fulltext_query(
    question: str
):

    tokens = re.findall(
        r"[A-Za-z]+",
        question.lower()
    )

    useful_tokens = [

        token

        for token in tokens

        if (
            token not in STOP_WORDS
            and
            len(token) > 2
        )
    ]


    # Remove duplicates while
    # preserving order

    useful_tokens = list(
        dict.fromkeys(
            useful_tokens
        )
    )


    return "|".join(
        useful_tokens
    )


# =====================================================
# Business Concept Full-Text Search
# =====================================================

def search_business_concepts_fulltext(
    question: str,
    top_k: int = 3
):

    search_query = (
        build_fulltext_query(
            question
        )
    )


    if not search_query:

        return []


    graph = get_graph()


    result = graph.query(

        f"""
        CALL db.idx.fulltext.queryNodes(
            'BusinessConcept',
            $search_query
        )

        YIELD node, score

        RETURN
            node.id,
            node.name,
            node.description,
            node.semantic_text,
            score

        ORDER BY score DESC

        LIMIT {top_k}
        """,

        {
            "search_query":
                search_query
        }
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

                "fulltext_score":
                    row[4],

                "retrieval_source":
                    "fulltext"
            }
        )


    return concepts


# =====================================================
# Metric Full-Text Search
# =====================================================

def search_metrics_fulltext(
    question: str,
    top_k: int = 3
):

    search_query = (
        build_fulltext_query(
            question
        )
    )


    if not search_query:

        return []


    graph = get_graph()


    result = graph.query(

        f"""
        CALL db.idx.fulltext.queryNodes(
            'Metric',
            $search_query
        )

        YIELD node, score

        RETURN
            node.id,
            node.name,
            node.description,
            node.expression,
            node.semantic_text,
            score

        ORDER BY score DESC

        LIMIT {top_k}
        """,

        {
            "search_query":
                search_query
        }
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

                "fulltext_score":
                    row[5],

                "retrieval_source":
                    "fulltext"
            }
        )


    return metrics