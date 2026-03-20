from dagster import op
import math
import os
import uuid
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone

from skyfield.api import EarthSatellite, load, wgs84


@op(required_resource_keys={"trino"})
def fetch_latest_tles_for_positions(context):
    conn = context.resources.trino
    cur = conn.cursor()

    query = """
    SELECT
        norad_id,
        name,
        tle_line1,
        tle_line2,
        inclination,
        raan,
        eccentricity,
        argument_of_perigee,
        mean_anomaly,
        mean_motion,
        epoch
    FROM (
        SELECT
            norad_id,
            name,
            tle_line1,
            tle_line2,
            inclination,
            raan,
            eccentricity,
            argument_of_perigee,
            mean_anomaly,
            mean_motion,
            epoch,
            row_number() OVER (
                PARTITION BY norad_id
                ORDER BY ingestion_time DESC
            ) AS rn
        FROM satellites_tle
        WHERE tle_line1 IS NOT NULL
          AND tle_line2 IS NOT NULL
    )
    WHERE rn = 1
    """

    cur.execute(query)
    rows = cur.fetchall()

    result = []
    for row in rows:
        result.append(
            {
                "norad_id": row[0],
                "object_name": row[1],
                "tle_line1": row[2],
                "tle_line2": row[3],
                "inclination": row[4],
                "raan": row[5],
                "eccentricity": row[6],
                "argument_of_perigee": row[7],
                "mean_anomaly": row[8],
                "mean_motion": row[9],
                "epoch": row[10],
            }
        )

    context.log.info(f"{len(result)} TLEs mais recentes carregados para cálculo de posição")
    return result


@op
def calculate_satellite_positions(context, tle_rows):
    if not tle_rows:
        context.log.info("Nenhum TLE para calcular posição.")
        return []

    ts = load.timescale()
    position_timestamp = datetime.now(timezone.utc)
    t = ts.from_datetime(position_timestamp)

    run_id = str(uuid.uuid4())
    ingestion_time = datetime.now(timezone.utc)

    positions = []

    for row in tle_rows:
        try:
            satellite = EarthSatellite(
                row["tle_line1"],
                row["tle_line2"],
                row["object_name"] or str(row["norad_id"]),
                ts,
            )

            geocentric = satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)

            velocity_vector = geocentric.velocity.km_per_s
            velocity_km_s = math.sqrt(
                velocity_vector[0] ** 2
                + velocity_vector[1] ** 2
                + velocity_vector[2] ** 2
            )

            positions.append(
                {
                    "norad_id": row["norad_id"],
                    "object_name": row["object_name"],
                    "position_timestamp": position_timestamp,
                    "latitude": subpoint.latitude.degrees,
                    "longitude": subpoint.longitude.degrees,
                    "altitude_km": subpoint.elevation.km,
                    "velocity_km_s": velocity_km_s,
                    "inclination": row["inclination"],
                    "raan": row["raan"],
                    "eccentricity": row["eccentricity"],
                    "argument_of_perigee": row["argument_of_perigee"],
                    "mean_anomaly": row["mean_anomaly"],
                    "mean_motion": row["mean_motion"],
                    "epoch": row["epoch"],
                    "ingestion_time": ingestion_time,
                    "run_id": run_id,
                }
            )
        except Exception as e:
            context.log.warning(
                f"Falha ao calcular posição do NORAD {row['norad_id']}: {e}"
            )

    context.log.info(f"{len(positions)} posições calculadas")
    return positions


@op
def write_satellites_position_to_minio(context, rows):
    if not rows:
        context.log.info("Nenhuma posição para gravar.")
        return None

    s3_endpoint = os.environ["S3_ENDPOINT"]
    s3_access_key = os.environ["S3_ACCESS_KEY"]
    s3_secret_key = os.environ["S3_SECRET_KEY"]
    s3_bucket = os.environ["S3_BUCKET"]

    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_folder = str(uuid.uuid4())
    file_id = str(uuid.uuid4())

    local_path = f"/tmp/satellites_position_{file_id}.parquet"
    s3_key = (
        f"stage/satellites_position/run_date={run_date}/"
        f"run_id={run_folder}/part-{file_id}.parquet"
    )

    table = pa.Table.from_pylist(rows)
    pq.write_table(table, local_path, compression="zstd")

    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        region_name="us-east-1",
    )

    s3.upload_file(local_path, s3_bucket, s3_key)

    s3_path = f"s3://{s3_bucket}/{s3_key}"
    context.log.info(f"Arquivo de posição gravado no MinIO: {s3_path}")
    return s3_path


@op(required_resource_keys={"trino"})
def register_position_parquet_in_iceberg(context, parquet_path):
    if not parquet_path:
        context.log.info("Nenhum parquet de posição para registrar.")
        return

    conn = context.resources.trino
    cur = conn.cursor()

    location = parquet_path.rsplit("/", 1)[0]

    query = f"""
    ALTER TABLE satellites_position
    EXECUTE add_files(
        location => '{location}',
        format => 'PARQUET'
    )
    """

    cur.execute(query)
    context.log.info(f"Parquet de posição registrado no Iceberg: {location}")