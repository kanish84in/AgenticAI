from pprint import pprint


from graph.semantic_retriever import (
    retrieve_semantic_context,
    semantic_context_to_text
)


# =====================================================
# Test Question
# =====================================================

question = (
    "Which listeners generate the most income?"
)


# =====================================================
# Retrieve
# =====================================================

context = (
    retrieve_semantic_context(
        question
    )
)


# =====================================================
# Question
# =====================================================

print(
    "\nQUESTION"
)

print(
    "=" * 70
)

print(
    question
)


# =====================================================
# Concepts
# =====================================================

print(
    "\nKEYWORD CONCEPTS"
)

print(
    "=" * 70
)

pprint(
    context.get(
        "keyword_concepts",
        []
    )
)


print(
    "\nFULLTEXT CONCEPTS"
)

pprint(
    context.get(
        "fulltext_concepts",
        []
    )
)


print(
    "\nVECTOR CONCEPTS"
)

pprint(
    context.get(
        "vector_concepts",
        []
    )
)


print(
    "\nFINAL CONCEPTS"
)

pprint(
    context.get(
        "concepts",
        []
    )
)


# =====================================================
# Metrics
# =====================================================

print(
    "\nKEYWORD METRICS"
)

print(
    "=" * 70
)

pprint(
    context.get(
        "keyword_metrics",
        []
    )
)


print(
    "\nFULLTEXT METRICS"
)

pprint(
    context.get(
        "fulltext_metrics",
        []
    )
)


print(
    "\nVECTOR METRICS"
)

pprint(
    context.get(
        "vector_metrics",
        []
    )
)


print(
    "\nFINAL METRICS"
)

pprint(
    context.get(
        "metrics",
        []
    )
)


print(
    "\nMETRIC INTENT"
)

print(
    context.get(
        "metric_intent"
    )
)


# =====================================================
# Tables
# =====================================================

print(
    "\nCONCEPT TABLES"
)

print(
    "=" * 70
)

pprint(
    context.get(
        "concept_tables",
        []
    )
)


print(
    "\nMETRIC TABLES"
)

pprint(
    context.get(
        "metric_tables",
        []
    )
)


print(
    "\nDIRECT TABLES"
)

pprint(
    context.get(
        "direct_tables",
        []
    )
)


print(
    "\nSEED TABLES"
)

pprint(
    context.get(
        "seed_tables",
        []
    )
)


print(
    "\nFINAL TABLES"
)

pprint(
    context.get(
        "tables",
        []
    )
)


# =====================================================
# Join Paths
# =====================================================

print(
    "\nJOIN PATHS"
)

print(
    "=" * 70
)

pprint(
    context.get(
        "join_paths",
        []
    )
)


# =====================================================
# Columns
# =====================================================

print(
    "\nCOLUMNS"
)

print(
    "=" * 70
)

pprint(
    context.get(
        "columns",
        {}
    )
)


# =====================================================
# LLM Context
# =====================================================

print(
    "\nLLM CONTEXT"
)

print(
    "=" * 70
)

print(
    semantic_context_to_text(
        context
    )
)