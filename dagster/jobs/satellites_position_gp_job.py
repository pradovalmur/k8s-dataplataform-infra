from dagster import job
from ops.satellites_position_gp_ops import (
    fetch_latest_gp_for_positions,
    calculate_satellite_positions_gp,
    write_satellites_position_gp_to_minio,
    register_position_gp_parquet_in_iceberg,
)


@job
def ingest_satellites_position_gp():
    gp_rows = fetch_latest_gp_for_positions()
    positions = calculate_satellite_positions_gp(gp_rows)
    parquet_path = write_satellites_position_gp_to_minio(positions)
    register_position_gp_parquet_in_iceberg(parquet_path)