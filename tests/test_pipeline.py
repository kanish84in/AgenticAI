from database.db import (
    get_schema_text,
    execute_query
)

from llm.sql_generator import (
    generate_sql
)


question = """
Show the top 5 artists
by number of tracks
"""


print("\nQUESTION")
print("=" * 50)

print(question)


schema = get_schema_text()


print("\nGENERATING SQL...")
print("=" * 50)


generation = generate_sql(
    question=question,
    schema=schema
)


print("\nGENERATED SQL")
print("=" * 50)

print(generation.sql)


print("\nEXPLANATION")
print("=" * 50)

print(generation.explanation)


print("\nEXECUTING SQL")
print("=" * 50)


results = execute_query(
    generation.sql
)


for row in results["rows"]:
    print(row)