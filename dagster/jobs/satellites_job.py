from dagster import job
from ops.satellites_ops import (
    fetch_satellites,
    write_satellites_to_minio,
    register_parquet_in_iceberg,
)

@job
def ingest_satellites():
    rows = fetch_satellites()
    parquet_path = write_satellites_to_minio(rows)
    register_parquet_in_iceberg(parquet_path)