from dagster import job
from ops.satellites_gp_raw_ops import (
    fetch_space_track_gp_raw,
    write_space_track_gp_raw_to_minio,
    register_space_track_gp_raw_in_iceberg,
)

@job
def ingest_space_track_gp_raw():
    rows = fetch_space_track_gp_raw()
    parquet_path = write_space_track_gp_raw_to_minio(rows)
    register_space_track_gp_raw_in_iceberg(parquet_path)