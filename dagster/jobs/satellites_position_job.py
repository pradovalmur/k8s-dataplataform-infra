from dagster import job
from ops.satellites_position_ops import (
    fetch_latest_tles_for_positions,
    calculate_satellite_positions,
    write_satellites_position_to_minio,
    register_position_parquet_in_iceberg,
)

@job
def ingest_satellites_position():
    tle_rows = fetch_latest_tles_for_positions()
    positions = calculate_satellite_positions(tle_rows)
    parquet_path = write_satellites_position_to_minio(positions)
    register_position_parquet_in_iceberg(parquet_path)