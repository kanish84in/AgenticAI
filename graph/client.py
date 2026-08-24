from falkordb import FalkorDB

from app.config import (
    FALKORDB_HOST,
    FALKORDB_PORT,
    FALKORDB_GRAPH
)


db = FalkorDB(
    host=FALKORDB_HOST,
    port=FALKORDB_PORT
)


def get_graph():

    return db.select_graph(
        FALKORDB_GRAPH
    )