import sqlite3

connection = sqlite3.connect("../data/chinook.db")

cursor = connection.cursor()

query = """
SELECT Name
FROM Artist
LIMIT 10
"""

cursor.execute(query)

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()