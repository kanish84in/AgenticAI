from database.db import get_connection
from graph.client import get_graph


DATABASE_NAME = "chinook"


def reset_graph():

    graph = get_graph()

    try:
        graph.delete()

        print(
            "Existing semantic graph deleted."
        )

    except Exception:
        # Graph might not exist yet.
        pass


def create_database_node(graph):

    graph.query(
        """
        MERGE (d:Database {name: $name})
        SET d.type = $type
        """,
        {
            "name": DATABASE_NAME,
            "type": "SQLite"
        }
    )


def load_tables_and_columns(graph):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        print(
            f"Found {len(tables)} tables."
        )

        for table_name in tables:

            print(
                f"Loading table: {table_name}"
            )

            table_id = (
                f"table:{table_name}"
            )

            # -----------------------------
            # Table node
            # -----------------------------

            graph.query(
                """
                MERGE (t:Table {id: $id})

                SET
                    t.name = $name,
                    t.database = $database
                """,
                {
                    "id": table_id,
                    "name": table_name,
                    "database": DATABASE_NAME
                }
            )

            # -----------------------------
            # Database → Table
            # -----------------------------

            graph.query(
                """
                MATCH
                    (d:Database {name: $database}),
                    (t:Table {id: $table_id})

                MERGE
                    (d)-[:HAS_TABLE]->(t)
                """,
                {
                    "database": DATABASE_NAME,
                    "table_id": table_id
                }
            )

            safe_table_name = (
                table_name.replace(
                    '"',
                    '""'
                )
            )

            columns = connection.execute(
                f"""
                PRAGMA table_info(
                    "{safe_table_name}"
                )
                """
            ).fetchall()

            for column in columns:

                column_name = column[1]
                data_type = column[2]
                primary_key = bool(column[5])

                column_id = (
                    f"column:"
                    f"{table_name}."
                    f"{column_name}"
                )

                # -------------------------
                # Column node
                # -------------------------

                graph.query(
                    """
                    MERGE
                        (c:Column {id: $id})

                    SET
                        c.name = $name,
                        c.table = $table,
                        c.data_type = $data_type,
                        c.primary_key = $primary_key
                    """,
                    {
                        "id": column_id,
                        "name": column_name,
                        "table": table_name,
                        "data_type": data_type,
                        "primary_key": primary_key
                    }
                )

                # -------------------------
                # Table → Column
                # -------------------------

                graph.query(
                    """
                    MATCH
                        (t:Table {id: $table_id}),
                        (c:Column {id: $column_id})

                    MERGE
                        (t)-[:HAS_COLUMN]->(c)
                    """,
                    {
                        "table_id": table_id,
                        "column_id": column_id
                    }
                )

    finally:

        connection.close()


def load_foreign_keys(graph):

    connection = get_connection()

    try:

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        for table_row in tables:

            source_table = table_row[0]

            safe_table_name = (
                source_table.replace(
                    '"',
                    '""'
                )
            )

            foreign_keys = connection.execute(
                f"""
                PRAGMA foreign_key_list(
                    "{safe_table_name}"
                )
                """
            ).fetchall()

            for fk in foreign_keys:

                target_table = fk[2]
                source_column = fk[3]
                target_column = fk[4]

                source_column_id = (
                    f"column:"
                    f"{source_table}."
                    f"{source_column}"
                )

                target_column_id = (
                    f"column:"
                    f"{target_table}."
                    f"{target_column}"
                )

                # -------------------------
                # Column FK relationship
                # -------------------------

                graph.query(
                    """
                    MATCH
                        (
                            source:Column {
                                id: $source_id
                            }
                        ),
                        (
                            target:Column {
                                id: $target_id
                            }
                        )

                    MERGE
                        (source)
                        -[:REFERENCES]->
                        (target)
                    """,
                    {
                        "source_id":
                            source_column_id,

                        "target_id":
                            target_column_id
                    }
                )

                # -------------------------
                # Table-level join
                # relationship
                # -------------------------

                graph.query(
                    """
                    MATCH
                        (
                            source:Table {
                                id: $source_table_id
                            }
                        ),
                        (
                            target:Table {
                                id: $target_table_id
                            }
                        )

                    MERGE
                        (source)
                        -[
                            r:JOINS_TO
                        ]->
                        (target)

                    SET
                        r.source_column =
                            $source_column,

                        r.target_column =
                            $target_column,

                        r.weight = 1
                    """,
                    {
                        "source_table_id":
                            f"table:{source_table}",

                        "target_table_id":
                            f"table:{target_table}",

                        "source_column":
                            source_column,

                        "target_column":
                            target_column
                    }
                )

                print(
                    f"FK: "
                    f"{source_table}.{source_column}"
                    f" -> "
                    f"{target_table}.{target_column}"
                )

    finally:

        connection.close()



def load_business_semantics(graph):

    concepts = {

        # =================================================
        # Customer
        # =================================================

        "Customer": {

            "description":
                (
                    "A customer or listener "
                    "who purchases music."
                ),

            "synonyms": [

                "customer",
                "customers",

                "client",
                "clients",

                "buyer",
                "buyers",

                "listener",
                "listeners"
            ],

            # Map the concept only to its
            # primary entity table.
            #
            # Invoice will be discovered through
            # metrics / joins when required.

            "tables": [
                "Customer"
            ]
        },


        # =================================================
        # Artist
        # =================================================

        "Artist": {

            "description":
                "A music artist or performer.",

            "synonyms": [

                "artist",
                "artists",

                "performer",
                "performers",

                "band",
                "bands"
            ],

            "tables": [
                "Artist"
            ]
        },


        # =================================================
        # Album
        # =================================================

        "Album": {

            "description":
                "A music album.",

            "synonyms": [

                "album",
                "albums"
            ],

            "tables": [
                "Album"
            ]
        },


        # =================================================
        # Track
        # =================================================

        "Track": {

            "description":
                "A music track or song.",

            "synonyms": [

                "track",
                "tracks",

                "song",
                "songs",

                "music"
            ],

            "tables": [
                "Track"
            ]
        },


        # =================================================
        # Genre
        # =================================================

        "Genre": {

            "description":
                "Music genre or category.",

            "synonyms": [

                "genre",
                "genres",

                "category",
                "categories",

                "music type"
            ],

            "tables": [
                "Genre"
            ]
        },


        # =================================================
        # Country
        # =================================================

        "Country": {

            "description":
                (
                    "Geographic country associated "
                    "with customers or invoices."
                ),

            "synonyms": [

                "country",
                "countries",

                "nation",
                "nations",

                "location",
                "geography"
            ],

            # Country is a semantic concept,
            # not an actual Chinook table.

            "tables": [
                "Customer",
                "Invoice"
            ]
        }
    }


    # =====================================================
    # Create BusinessConcept Nodes
    # =====================================================

    for concept_name, metadata in concepts.items():

        concept_id = (
            f"concept:{concept_name.lower()}"
        )


        graph.query(

            """
            MERGE
                (
                    c:BusinessConcept {
                        id: $id
                    }
                )

            SET
                c.name = $name,
                c.description = $description
            """,

            {
                "id":
                    concept_id,

                "name":
                    concept_name,

                "description":
                    metadata[
                        "description"
                    ]
            }
        )


        # =================================================
        # Create Synonym Nodes
        # =================================================

        for synonym in metadata[
            "synonyms"
        ]:

            synonym_id = (
                f"synonym:"
                f"{concept_name.lower()}:"
                f"{synonym.lower()}"
            )


            graph.query(

                """
                MERGE
                    (
                        s:Synonym {
                            id: $synonym_id
                        }
                    )

                SET
                    s.name = $synonym


                WITH s


                MATCH
                    (
                        c:BusinessConcept {
                            id: $concept_id
                        }
                    )


                MERGE
                    (c)-[:HAS_SYNONYM]->(s)
                """,

                {
                    "synonym_id":
                        synonym_id,

                    "synonym":
                        synonym,

                    "concept_id":
                        concept_id
                }
            )


        # =================================================
        # Concept -> Primary Table
        # =================================================

        for table_name in metadata[
            "tables"
        ]:

            graph.query(

                """
                MATCH
                    (
                        c:BusinessConcept {
                            id: $concept_id
                        }
                    ),

                    (
                        t:Table {
                            id: $table_id
                        }
                    )

                MERGE
                    (c)-[:MAPS_TO]->(t)
                """,

                {
                    "concept_id":
                        concept_id,

                    "table_id":
                        f"table:{table_name}"
                }
            )



def load_metrics(graph):

    # =====================================================
    # Revenue Metric
    # =====================================================

    metric_id = (
        "metric:revenue"
    )


    graph.query(

        """
        MERGE
            (
                m:Metric {
                    id: $id
                }
            )

        SET
            m.name = $name,
            m.description = $description,
            m.expression = $expression
        """,

        {
            "id":
                metric_id,

            "name":
                "Revenue",

            "description":
                (
                    "Total monetary value "
                    "of purchases."
                ),

            "expression":
                (
                    "SUM("
                    "InvoiceLine.UnitPrice * "
                    "InvoiceLine.Quantity"
                    ")"
                )
        }
    )


    # =====================================================
    # Revenue Synonyms
    # =====================================================

    revenue_synonyms = [

        "revenue",
        "revenues",

        "sales",
        "sales amount",

        "income",
        "earnings",

        "amount spent",

        "spend",
        "spending",
        "spent",

        "total amount",

        "purchase value",

        "money spent",
        "money generated"
    ]


    for synonym in revenue_synonyms:

        synonym_id = (
            "metric_synonym:"
            "revenue:"
            f"{synonym.lower()}"
        )


        graph.query(

            """
            MERGE
                (
                    s:Synonym {
                        id: $synonym_id
                    }
                )

            SET
                s.name = $synonym


            WITH s


            MATCH
                (
                    m:Metric {
                        id: $metric_id
                    }
                )


            MERGE
                (m)-[:HAS_SYNONYM]->(s)
            """,

            {
                "synonym_id":
                    synonym_id,

                "synonym":
                    synonym,

                "metric_id":
                    metric_id
            }
        )


    # =====================================================
    # Revenue -> Tables
    # =====================================================

    revenue_tables = [

        "Invoice",
        "InvoiceLine"
    ]


    for table_name in revenue_tables:

        graph.query(

            """
            MATCH
                (
                    m:Metric {
                        id: $metric_id
                    }
                ),

                (
                    t:Table {
                        id: $table_id
                    }
                )


            MERGE
                (m)-[:USES_TABLE]->(t)
            """,

            {
                "metric_id":
                    metric_id,

                "table_id":
                    f"table:{table_name}"
            }
        )



def load_semantic_graph():

    print(
        "\nBuilding FalkorDB semantic layer..."
    )

    reset_graph()

    graph = get_graph()

    print(
        "\n1. Creating database..."
    )

    create_database_node(
        graph
    )


    print(
        "\n2. Loading tables and columns..."
    )

    load_tables_and_columns(
        graph
    )


    print(
        "\n3. Loading foreign keys..."
    )

    load_foreign_keys(
        graph
    )


    print(
        "\n4. Loading business concepts..."
    )

    load_business_semantics(
        graph
    )


    print(
        "\n5. Loading metrics..."
    )

    load_metrics(
        graph
    )


    print(
        "\nSemantic graph created successfully!"
    )


if __name__ == "__main__":

    load_semantic_graph()