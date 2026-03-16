from dagster import job
from ops.satellites_catalog_ops import (
    fetch_satellites_catalog,
    write_satellites_catalog_to_minio,
    register_catalog_parquet_in_iceberg,
)

@job
def ingest_satellites_catalog():
    rows = fetch_satellites_catalog()
    parquet_path = write_satellites_catalog_to_minio(rows)
    register_catalog_parquet_in_iceberg(parquet_path)