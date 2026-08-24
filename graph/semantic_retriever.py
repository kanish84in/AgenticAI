import re

from itertools import combinations

from typing import Any


from app.config import (
    VECTOR_MIN_SCORE
)


from graph.client import (
    get_graph
)


from graph.vector_retriever import (
    search_business_concepts,
    search_metrics
)


from graph.fulltext_retriever import (
    search_business_concepts_fulltext,
    search_metrics_fulltext
)


# =====================================================
# Text Utilities
# =====================================================

def normalize_text(
    text: str
) -> str:

    if not text:
        return ""

    text = (
        text
        .lower()
        .strip()
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# =====================================================
# Term Matching
# =====================================================

def contains_term(
    question: str,
    term: str
) -> bool:

    question_normalized = (
        normalize_text(
            question
        )
    )

    term_normalized = (
        normalize_text(
            term
        )
    )


    if not term_normalized:
        return False


    # Multi-word phrase

    if " " in term_normalized:

        return (
            term_normalized
            in
            question_normalized
        )


    # Exact whole-word match

    pattern = (
        r"\b"
        +
        re.escape(
            term_normalized
        )
        +
        r"\b"
    )


    return (
        re.search(
            pattern,
            question_normalized
        )
        is not None
    )


# =====================================================
# Exact Business Concept Detection
# =====================================================

def detect_business_concepts(
    question: str
) -> list[
    dict[str, Any]
]:

    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (concept:BusinessConcept)

        OPTIONAL MATCH
            (concept)
            -[:HAS_SYNONYM]->
            (synonym:Synonym)

        RETURN
            concept.id,
            concept.name,
            concept.description,
            collect(synonym.name)
                AS synonyms,
            concept.semantic_text
        """
    )


    detected = []


    for row in result.result_set:

        concept_id = (
            row[0]
        )

        concept_name = (
            row[1]
        )

        description = (
            row[2]
        )

        synonyms = (
            row[3]
            or
            []
        )

        semantic_text = (
            row[4]
        )


        terms = [

            concept_name,

            *synonyms
        ]


        matched_terms = [

            term

            for term in terms

            if contains_term(
                question,
                term
            )
        ]


        if matched_terms:

            detected.append(

                {
                    "id":
                        concept_id,

                    "name":
                        concept_name,

                    "description":
                        description,

                    "semantic_text":
                        semantic_text,

                    "matched_terms":
                        matched_terms,

                    "retrieval_source":
                        "keyword"
                }
            )


    return detected


# =====================================================
# Exact Metric Detection
# =====================================================

def detect_metrics(
    question: str
) -> list[
    dict[str, Any]
]:

    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (metric:Metric)

        OPTIONAL MATCH
            (metric)
            -[:HAS_SYNONYM]->
            (synonym:Synonym)

        RETURN
            metric.id,
            metric.name,
            metric.description,
            metric.expression,
            collect(synonym.name)
                AS synonyms,
            metric.semantic_text
        """
    )


    detected = []


    for row in result.result_set:

        metric_id = (
            row[0]
        )

        metric_name = (
            row[1]
        )

        description = (
            row[2]
        )

        expression = (
            row[3]
        )

        synonyms = (
            row[4]
            or
            []
        )

        semantic_text = (
            row[5]
        )


        terms = [

            metric_name,

            *synonyms
        ]


        matched_terms = [

            term

            for term in terms

            if contains_term(
                question,
                term
            )
        ]


        if matched_terms:

            detected.append(

                {
                    "id":
                        metric_id,

                    "name":
                        metric_name,

                    "description":
                        description,

                    "expression":
                        expression,

                    "semantic_text":
                        semantic_text,

                    "matched_terms":
                        matched_terms,

                    "retrieval_source":
                        "keyword"
                }
            )


    return detected


# =====================================================
# Metric Intent Detection
# =====================================================

SEMANTIC_METRIC_HINTS = {

    "revenue",
    "revenues",

    "sales",
    "sale",

    "income",
    "earnings",

    "spend",
    "spending",
    "spent",

    "amount spent",

    "purchase value",

    "money spent",

    "money generated",

    "total sales",

    "total revenue"
}


def question_has_metric_intent(
    question: str
) -> bool:

    return any(

        contains_term(
            question,
            hint
        )

        for hint
        in SEMANTIC_METRIC_HINTS
    )


# =====================================================
# Hybrid Rank Fusion
# =====================================================

def fuse_semantic_candidates(
    keyword_items,
    fulltext_items,
    vector_items,
    min_vector_score=None,
    top_n=2
):

    if min_vector_score is None:

        min_vector_score = (
            VECTOR_MIN_SCORE
        )


    candidates = {}


    def ensure_candidate(
        item
    ):

        item_id = (
            item["id"]
        )


        if item_id not in candidates:

            candidates[
                item_id
            ] = {

                **item,

                "fusion_score":
                    0.0,

                "retrieval_sources":
                    []
            }


        else:

            existing = (
                candidates[
                    item_id
                ]
            )


            for key, value in item.items():

                if (
                    key not in existing
                    or
                    existing[key] is None
                ):

                    existing[
                        key
                    ] = value


        return (
            candidates[
                item_id
            ]
        )


    # =================================================
    # Keyword
    # =================================================

    for item in keyword_items:

        candidate = (
            ensure_candidate(
                item
            )
        )


        candidate[
            "fusion_score"
        ] += 1.0


        if (
            "keyword"
            not in
            candidate[
                "retrieval_sources"
            ]
        ):

            candidate[
                "retrieval_sources"
            ].append(
                "keyword"
            )


    # =================================================
    # Full-text
    # =================================================

    for rank, item in enumerate(
        fulltext_items,
        start=1
    ):

        candidate = (
            ensure_candidate(
                item
            )
        )


        candidate[
            "fusion_score"
        ] += (
            0.7
            /
            (
                rank + 1
            )
        )


        if (
            "fulltext"
            not in
            candidate[
                "retrieval_sources"
            ]
        ):

            candidate[
                "retrieval_sources"
            ].append(
                "fulltext"
            )


        candidate[
            "fulltext_score"
        ] = item.get(
            "fulltext_score"
        )


    # =================================================
    # Vector
    # =================================================

    for rank, item in enumerate(
        vector_items,
        start=1
    ):

        vector_score = (
            item.get(
                "similarity_score",
                0
            )
            or
            0
        )


        if (
            vector_score
            <
            min_vector_score
        ):

            continue


        candidate = (
            ensure_candidate(
                item
            )
        )


        candidate[
            "fusion_score"
        ] += (
            0.6
            /
            (
                rank + 1
            )
        )


        if (
            "vector"
            not in
            candidate[
                "retrieval_sources"
            ]
        ):

            candidate[
                "retrieval_sources"
            ].append(
                "vector"
            )


        candidate[
            "similarity_score"
        ] = vector_score


    # =================================================
    # Sort
    # =================================================

    ranked = sorted(

        candidates.values(),

        key=lambda item:
            item[
                "fusion_score"
            ],

        reverse=True
    )


    keyword_ids = {

        item[
            "id"
        ]

        for item
        in keyword_items
    }


    selected = []


    # Exact matches always survive.

    for item in ranked:

        if (
            item[
                "id"
            ]
            in
            keyword_ids
        ):

            selected.append(
                item
            )


    selected_ids = {

        item[
            "id"
        ]

        for item
        in selected
    }


    target_count = max(
        top_n,
        len(
            keyword_ids
        )
    )


    for item in ranked:

        if (
            item[
                "id"
            ]
            in
            selected_ids
        ):

            continue


        selected.append(
            item
        )


        selected_ids.add(
            item[
                "id"
            ]
        )


        if (
            len(
                selected
            )
            >=
            target_count
        ):

            break


    # =================================================
    # Retrieval source label
    # =================================================

    for item in selected:

        sources = (
            item.get(
                "retrieval_sources",
                []
            )
        )


        if len(
            sources
        ) == 1:

            item[
                "retrieval_source"
            ] = sources[
                0
            ]


        elif len(
            sources
        ) > 1:

            item[
                "retrieval_source"
            ] = "hybrid"


    return selected


# =====================================================
# Concept -> Tables
# =====================================================

def get_concept_tables(
    concepts
) -> set[str]:

    if not concepts:
        return set()


    graph = get_graph()

    tables = set()


    for concept in concepts:

        result = graph.query(

            """
            MATCH
                (
                    concept:BusinessConcept {
                        id: $concept_id
                    }
                )
                -[:MAPS_TO]->
                (table:Table)

            RETURN
                table.name
            """,

            {
                "concept_id":
                    concept[
                        "id"
                    ]
            }
        )


        for row in result.result_set:

            tables.add(
                row[0]
            )


    return tables


# =====================================================
# Metric -> Tables
# =====================================================

def get_metric_tables(
    metrics
) -> set[str]:

    if not metrics:
        return set()


    graph = get_graph()

    tables = set()


    for metric in metrics:

        result = graph.query(

            """
            MATCH
                (
                    metric:Metric {
                        id: $metric_id
                    }
                )
                -[:USES_TABLE]->
                (table:Table)

            RETURN
                table.name
            """,

            {
                "metric_id":
                    metric[
                        "id"
                    ]
            }
        )


        for row in result.result_set:

            tables.add(
                row[0]
            )


    return tables


# =====================================================
# Direct Physical Table Detection
# =====================================================

def detect_direct_tables(
    question: str
) -> set[str]:

    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (table:Table)

        RETURN
            table.name
        """
    )


    detected = set()


    for row in result.result_set:

        table_name = (
            row[0]
        )


        if contains_term(
            question,
            table_name
        ):

            detected.add(
                table_name
            )


    return detected


# =====================================================
# FalkorDB Shortest Join Path
# =====================================================

def find_shortest_join_path(
    source_table: str,
    target_table: str
):

    if (
        source_table
        ==
        target_table
    ):

        return [
            source_table
        ]


    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (
                source:Table {
                    name: $source
                }
            ),

            (
                target:Table {
                    name: $target
                }
            )


        CALL algo.SPpaths({

            sourceNode:
                source,

            targetNode:
                target,

            relTypes:
                ['JOINS_TO'],

            weightProp:
                'weight',

            relDirection:
                'both',

            maxLen:
                6,

            pathCount:
                1
        })


        YIELD
            path,
            pathWeight


        RETURN [

            node
            IN nodes(path)
            |
            node.name

        ] AS table_path
        """,

        {
            "source":
                source_table,

            "target":
                target_table
        }
    )


    if not result.result_set:

        return []


    return (
        result.result_set[
            0
        ][0]
        or
        []
    )


# =====================================================
# Expand Tables With Join Paths
# =====================================================

def expand_with_join_paths(
    seed_tables
):

    seed_tables = sorted(
        set(
            seed_tables
        )
    )


    all_tables = set(
        seed_tables
    )


    join_paths = []


    if len(
        seed_tables
    ) < 2:

        return (
            all_tables,
            join_paths
        )


    for source, target in combinations(
        seed_tables,
        2
    ):

        path = (
            find_shortest_join_path(
                source,
                target
            )
        )


        if path:

            join_paths.append(
                path
            )


            all_tables.update(
                path
            )


    return (
        all_tables,
        join_paths
    )


# =====================================================
# Join Relationships
# =====================================================

def get_join_relationships(
    tables
):

    tables = sorted(
        set(
            tables
        )
    )


    if not tables:
        return []


    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (source:Table)
            -[
                relationship:JOINS_TO
            ]->
            (target:Table)

        WHERE
            source.name IN $tables

        AND
            target.name IN $tables


        RETURN
            source.name,
            relationship.source_column,
            target.name,
            relationship.target_column
        """,

        {
            "tables":
                tables
        }
    )


    joins = []

    seen = set()


    for row in result.result_set:

        join = {

            "source_table":
                row[0],

            "source_column":
                row[1],

            "target_table":
                row[2],

            "target_column":
                row[3]
        }


        key = (

            join[
                "source_table"
            ],

            join[
                "source_column"
            ],

            join[
                "target_table"
            ],

            join[
                "target_column"
            ]
        )


        if key not in seen:

            seen.add(
                key
            )

            joins.append(
                join
            )


    return joins


# =====================================================
# Table Columns
# =====================================================

def get_table_columns(
    tables
):

    tables = sorted(
        set(
            tables
        )
    )


    if not tables:
        return {}


    graph = get_graph()


    result = graph.query(

        """
        MATCH
            (table:Table)
            -[:HAS_COLUMN]->
            (column:Column)

        WHERE
            table.name IN $tables


        RETURN
            table.name,
            column.name,
            column.data_type,
            column.primary_key


        ORDER BY
            table.name,
            column.name
        """,

        {
            "tables":
                tables
        }
    )


    columns = {}


    for row in result.result_set:

        table_name = (
            row[0]
        )


        if (
            table_name
            not in columns
        ):

            columns[
                table_name
            ] = []


        columns[
            table_name
        ].append(

            {
                "name":
                    row[1],

                "type":
                    row[2],

                "primary_key":
                    bool(
                        row[3]
                    )
            }
        )


    return columns


# =====================================================
# Main Semantic Retrieval
# =====================================================

def retrieve_semantic_context(
    question: str
):

    # =================================================
    # 1. BUSINESS CONCEPTS
    # =================================================

    keyword_concepts = (
        detect_business_concepts(
            question
        )
    )


    # Exact business vocabulary is authoritative.

    if keyword_concepts:

        concepts = (
            keyword_concepts
        )

        fulltext_concepts = []

        vector_concepts = []


    else:

        fulltext_concepts = (
            search_business_concepts_fulltext(
                question
            )
        )


        vector_concepts = (
            search_business_concepts(
                question
            )
        )


        concepts = (
            fuse_semantic_candidates(

                keyword_items=[],

                fulltext_items=
                    fulltext_concepts,

                vector_items=
                    vector_concepts,

                min_vector_score=
                    VECTOR_MIN_SCORE,

                top_n=
                    2
            )
        )


    # =================================================
    # 2. METRICS
    # =================================================

    keyword_metrics = (
        detect_metrics(
            question
        )
    )


    # Exact metric vocabulary is authoritative.

    if keyword_metrics:

        metrics = (
            keyword_metrics
        )

        fulltext_metrics = []

        vector_metrics = []

        metric_intent = True


    else:

        metric_intent = (
            question_has_metric_intent(
                question
            )
        )


        if metric_intent:

            fulltext_metrics = (
                search_metrics_fulltext(
                    question
                )
            )


            vector_metrics = (
                search_metrics(
                    question
                )
            )


            metrics = (
                fuse_semantic_candidates(

                    keyword_items=[],

                    fulltext_items=
                        fulltext_metrics,

                    vector_items=
                        vector_metrics,

                    min_vector_score=
                        VECTOR_MIN_SCORE,

                    top_n=
                        1
                )
            )


        else:

            fulltext_metrics = []

            vector_metrics = []

            metrics = []


    # =================================================
    # 3. TABLE DISCOVERY
    # =================================================

    concept_tables = (
        get_concept_tables(
            concepts
        )
    )


    metric_tables = (
        get_metric_tables(
            metrics
        )
    )


    direct_tables = (
        detect_direct_tables(
            question
        )
    )


    seed_tables = (

        concept_tables

        |

        metric_tables

        |

        direct_tables
    )


    # =================================================
    # 4. JOIN EXPANSION
    # =================================================

    (
        expanded_tables,
        join_paths

    ) = expand_with_join_paths(
        seed_tables
    )


    # =================================================
    # 5. JOIN METADATA
    # =================================================

    joins = (
        get_join_relationships(
            expanded_tables
        )
    )


    # =================================================
    # 6. COLUMN METADATA
    # =================================================

    columns = (
        get_table_columns(
            expanded_tables
        )
    )


    # =================================================
    # 7. FINAL RESULT
    # =================================================

    return {

        "concepts":
            concepts,

        "metrics":
            metrics,

        "tables":
            sorted(
                expanded_tables
            ),

        "join_paths":
            join_paths,

        "joins":
            joins,

        "columns":
            columns,


        # ---------------------------------------------
        # Diagnostic information
        # ---------------------------------------------

        "metric_intent":
            metric_intent,

        "keyword_concepts":
            keyword_concepts,

        "fulltext_concepts":
            fulltext_concepts,

        "vector_concepts":
            vector_concepts,

        "keyword_metrics":
            keyword_metrics,

        "fulltext_metrics":
            fulltext_metrics,

        "vector_metrics":
            vector_metrics,

        "concept_tables":
            sorted(
                concept_tables
            ),

        "metric_tables":
            sorted(
                metric_tables
            ),

        "direct_tables":
            sorted(
                direct_tables
            ),

        "seed_tables":
            sorted(
                seed_tables
            )
    }


# =====================================================
# Convert Semantic Context to LLM Prompt
# =====================================================

def semantic_context_to_text(
    semantic_context
) -> str:

    parts = []


    # =================================================
    # Concepts
    # =================================================

    concepts = (
        semantic_context.get(
            "concepts",
            []
        )
    )


    if concepts:

        parts.append(
            "BUSINESS CONCEPTS"
        )

        parts.append(
            "================="
        )


        for concept in concepts:

            parts.append(

                f"- "
                f"{concept.get('name')}: "
                f"{concept.get('description', '')}"
            )


        parts.append(
            ""
        )


    # =================================================
    # Metrics
    # =================================================

    metrics = (
        semantic_context.get(
            "metrics",
            []
        )
    )


    if metrics:

        parts.append(
            "AUTHORITATIVE BUSINESS METRICS"
        )

        parts.append(
            "=============================="
        )


        parts.append(
            (
                "The following metric definitions "
                "are authoritative."
            )
        )


        for metric in metrics:

            parts.append(
                (
                    f"- Metric: "
                    f"{metric.get('name')}"
                )
            )


            if metric.get(
                "description"
            ):

                parts.append(
                    (
                        f"  Description: "
                        f"{metric.get('description')}"
                    )
                )


            if metric.get(
                "expression"
            ):

                parts.append(
                    (
                        f"  Formula: "
                        f"{metric.get('expression')}"
                    )
                )


        parts.append(
            ""
        )


    # =================================================
    # Tables and Columns
    # =================================================

    tables = (
        semantic_context.get(
            "tables",
            []
        )
    )


    columns = (
        semantic_context.get(
            "columns",
            {}
        )
    )


    if tables:

        parts.append(
            "DATABASE TABLES"
        )

        parts.append(
            "==============="
        )


        for table in tables:

            parts.append(
                f"\nTABLE: {table}"
            )


            table_columns = (
                columns.get(
                    table,
                    []
                )
            )


            if table_columns:

                parts.append(
                    "COLUMNS:"
                )


                for column in table_columns:

                    description = (
                        f"- "
                        f"{column.get('name')} "
                        f"{column.get('type') or ''}"
                    ).strip()


                    if column.get(
                        "primary_key"
                    ):

                        description += (
                            " PRIMARY KEY"
                        )


                    parts.append(
                        description
                    )


        parts.append(
            ""
        )


    # =================================================
    # Joins
    # =================================================

    joins = (
        semantic_context.get(
            "joins",
            []
        )
    )


    if joins:

        parts.append(
            "VALID JOIN RELATIONSHIPS"
        )

        parts.append(
            "========================"
        )


        for join in joins:

            parts.append(
                (
                    f"- "
                    f"{join.get('source_table')}."
                    f"{join.get('source_column')} "
                    f"= "
                    f"{join.get('target_table')}."
                    f"{join.get('target_column')}"
                )
            )


        parts.append(
            ""
        )


    # =================================================
    # Join Paths
    # =================================================

    join_paths = (
        semantic_context.get(
            "join_paths",
            []
        )
    )


    if join_paths:

        parts.append(
            "GRAPH JOIN PATHS"
        )

        parts.append(
            "================"
        )


        for path in join_paths:

            parts.append(
                "- "
                +
                " -> ".join(
                    path
                )
            )


        parts.append(
            ""
        )


    # =================================================
    # Semantic Rules
    # =================================================

    parts.append(
        "SEMANTIC RULES"
    )

    parts.append(
        "=============="
    )


    parts.append(
        (
            "- Use only the tables, columns, joins "
            "and business metrics provided above."
        )
    )


    parts.append(
        (
            "- Do not invent business metrics that "
            "the user did not request."
        )
    )


    parts.append(
        (
            "- The word 'top' alone does not imply "
            "Revenue, Sales or Spending."
        )
    )


    parts.append(
        (
            "- If no ranking metric is specified, "
            "do not invent one."
        )
    )


    if metrics:

        parts.append(
            (
                "- Metric formulas under "
                "AUTHORITATIVE BUSINESS METRICS "
                "must be treated as the source "
                "of truth."
            )
        )


    return "\n".join(
        parts
    )