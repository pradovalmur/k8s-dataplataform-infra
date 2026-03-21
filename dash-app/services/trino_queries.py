import os
import pandas as pd
import trino


def get_connection():
    return trino.dbapi.connect(
        host=os.getenv("TRINO_HOST", "trino.analytics.svc.cluster.local"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "dash"),
        catalog=os.getenv("TRINO_CATALOG", "iceberg"),
        schema=os.getenv("TRINO_SCHEMA", "space"),
    )


BASE_QUERY = """
SELECT
    norad_id,
    object_name,
    latitude,
    longitude,
    altitude_km,
    velocity_km_s,
    object_type,
    owner,
    launch_site,
    ops_status_code
FROM satellites_map_gp
"""


def load_satellites() -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql(BASE_QUERY, conn)


def load_filter_values() -> dict:
    conn = get_connection()

    queries = {
        "owner": """
            SELECT DISTINCT owner
            FROM satellites_map_gp
            WHERE owner IS NOT NULL
            ORDER BY 1
        """,
        "object_type": """
            SELECT DISTINCT object_type
            FROM satellites_map_gp
            WHERE object_type IS NOT NULL
            ORDER BY 1
        """,
        "launch_site": """
            SELECT DISTINCT launch_site
            FROM satellites_map_gp
            WHERE launch_site IS NOT NULL
            ORDER BY 1
        """,
        "ops_status_code": """
            SELECT DISTINCT ops_status_code
            FROM satellites_map_gp
            WHERE ops_status_code IS NOT NULL
            ORDER BY 1
        """,
    }

    result = {}
    for key, query in queries.items():
        df = pd.read_sql(query, conn)
        result[key] = df.iloc[:, 0].dropna().tolist()

    return result