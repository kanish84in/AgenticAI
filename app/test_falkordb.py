from falkordb import FalkorDB

db = FalkorDB(
    host="localhost",
    port=6379
)

graph = db.select_graph("text2sql")

graph.query("""
CREATE (:Table {
    name: 'Artist',
    description: 'Contains artist information'
})
""")

result = graph.query("""
MATCH (t:Table)
RETURN t.name
""")

for row in result.result_set:
    print(row)