from graph.client import get_graph


graph = get_graph()


print("\nTABLES")
print("=" * 60)

result = graph.query(
    """
    MATCH (t:Table)
    RETURN t.name
    ORDER BY t.name
    """
)

for row in result.result_set:
    print(row[0])


print("\nBUSINESS CONCEPTS")
print("=" * 60)

result = graph.query(
    """
    MATCH (c:BusinessConcept)
    RETURN c.name, c.description
    ORDER BY c.name
    """
)

for row in result.result_set:
    print(
        row[0],
        "-",
        row[1]
    )


print("\nMETRICS")
print("=" * 60)

result = graph.query(
    """
    MATCH (m:Metric)
    RETURN
        m.name,
        m.expression
    """
)

for row in result.result_set:
    print(row)


print("\nJOIN RELATIONSHIPS")
print("=" * 60)

result = graph.query(
    """
    MATCH
        (a:Table)
        -[r:JOINS_TO]->
        (b:Table)

    RETURN
        a.name,
        r.source_column,
        b.name,
        r.target_column

    ORDER BY
        a.name
    """
)

for row in result.result_set:

    print(
        f"{row[0]}.{row[1]}"
        f" -> "
        f"{row[2]}.{row[3]}"
    )