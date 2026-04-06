import os
import logging
import pandas as pd
import trino

logger = logging.getLogger(__name__)


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
    inclination,
    object_type,
    owner,
    launch_site,
    ops_status_code,
    starlink_group
FROM satellites_map_gp
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
LIMIT 5000
"""


def load_satellites() -> pd.DataFrame:
    conn = get_connection()
    try:
        logger.info("Loading satellite data from Trino")
        df = pd.read_sql(BASE_QUERY, conn)
        logger.info("Loaded %s satellite rows", len(df))
        return df
    finally:
        conn.close()


def load_filter_values() -> dict:
    queries = {
        "owner": """
            SELECT DISTINCT owner
            FROM satellites_map_gp
            WHERE owner IS NOT NULL
            ORDER BY 1
            LIMIT 500
        """,
        "object_type": """
            SELECT DISTINCT object_type
            FROM satellites_map_gp
            WHERE object_type IS NOT NULL
            ORDER BY 1
            LIMIT 100
        """,
    }

    result = {}

    for key, query in queries.items():
        conn = get_connection()
        try:
            logger.info("Loading filter values: %s", key)
            df = pd.read_sql(query, conn)
            result[key] = df.iloc[:, 0].dropna().tolist()
            logger.info("Loaded %s values for filter %s", len(result[key]), key)
        finally:
            conn.close()

    return result