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
def fetch_latest_gp_for_positions(context):
    conn = context.resources.trino
    cur = conn.cursor()

    query = """
    SELECT
        norad_cat_id,
        object_name,
        object_id,
        epoch,
        mean_motion,
        eccentricity,
        inclination,
        ra_of_asc_node,
        arg_of_pericenter,
        mean_anomaly,
        ephemeris_type,
        bstar,
        mean_motion_dot,
        mean_motion_ddot,
        classification_type,
        element_set_no,
        rev_at_epoch
    FROM (
        SELECT
            norad_cat_id,
            object_name,
            object_id,
            epoch,
            mean_motion,
            eccentricity,
            inclination,
            ra_of_asc_node,
            arg_of_pericenter,
            mean_anomaly,
            ephemeris_type,
            bstar,
            mean_motion_dot,
            mean_motion_ddot,
            classification_type,
            element_set_no,
            rev_at_epoch,
            row_number() OVER (
                PARTITION BY norad_cat_id
                ORDER BY ingestion_time DESC
            ) AS rn
        FROM satellites_gp_raw
        WHERE epoch IS NOT NULL
          AND norad_cat_id IS NOT NULL
          AND mean_motion IS NOT NULL
          AND eccentricity IS NOT NULL
          AND inclination IS NOT NULL
          AND ra_of_asc_node IS NOT NULL
          AND arg_of_pericenter IS NOT NULL
          AND mean_anomaly IS NOT NULL
    )
    WHERE rn = 1
    """

    cur.execute(query)
    rows = cur.fetchall()

    result = []
    for row in rows:
        result.append(
            {
                "NORAD_CAT_ID": int(row[0]) if row[0] is not None else None,
                "OBJECT_NAME": row[1],
                "OBJECT_ID": row[2],
                "EPOCH": row[3].isoformat() if row[3] else None,
                "MEAN_MOTION": float(row[4]) if row[4] is not None else None,
                "ECCENTRICITY": float(row[5]) if row[5] is not None else None,
                "INCLINATION": float(row[6]) if row[6] is not None else None,
                "RA_OF_ASC_NODE": float(row[7]) if row[7] is not None else None,
                "ARG_OF_PERICENTER": float(row[8]) if row[8] is not None else None,
                "MEAN_ANOMALY": float(row[9]) if row[9] is not None else None,
                "EPHEMERIS_TYPE": int(row[10]) if row[10] is not None else 0,
                "BSTAR": float(row[11]) if row[11] is not None else 0.0,
                "MEAN_MOTION_DOT": float(row[12]) if row[12] is not None else 0.0,
                "MEAN_MOTION_DDOT": float(row[13]) if row[13] is not None else 0.0,
                "CLASSIFICATION_TYPE": row[14] if row[14] else "U",
                "ELEMENT_SET_NO": int(row[15]) if row[15] is not None else 1,
                "REV_AT_EPOCH": int(row[16]) if row[16] is not None else 1,
            }
        )

    context.log.info(f"{len(result)} registros GP mais recentes carregados")
    return result


@op
def calculate_satellite_positions_gp(context, gp_rows):
    if not gp_rows:
        context.log.info("Nenhum GP para calcular posição.")
        return []

    ts = load.timescale()
    position_timestamp = datetime.now(timezone.utc)
    t = ts.from_datetime(position_timestamp)

    run_id = str(uuid.uuid4())
    ingestion_time = datetime.now(timezone.utc)

    positions = []

    for row in gp_rows:
        try:
            if "NORAD_CAT_ID" not in row:
                context.log.warning(
                    f"Row sem NORAD_CAT_ID. Chaves disponíveis: {list(row.keys())}"
                )
                continue

            satellite = EarthSatellite.from_omm(ts, row)
            geocentric = satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)

            velocity_vector = geocentric.velocity.km_per_s
            velocity_km_s = math.sqrt(
                velocity_vector[0] ** 2
                + velocity_vector[1] ** 2
                + velocity_vector[2] ** 2
            )

            lat = subpoint.latitude.degrees
            lon = subpoint.longitude.degrees
            alt = subpoint.elevation.km

            if (
                math.isnan(lat)
                or math.isnan(lon)
                or math.isnan(alt)
                or math.isnan(velocity_km_s)
            ):
                context.log.warning(
                    f"NORAD {row['NORAD_CAT_ID']} gerou NaN, ignorando"
                )
                continue

            positions.append(
                {
                    "norad_id": row["NORAD_CAT_ID"],
                    "object_name": row["OBJECT_NAME"],
                    "position_timestamp": position_timestamp,
                    "latitude": lat,
                    "longitude": lon,
                    "altitude_km": alt,
                    "velocity_km_s": velocity_km_s,
                    "inclination": row["INCLINATION"],
                    "ra_of_asc_node": row["RA_OF_ASC_NODE"],
                    "eccentricity": row["ECCENTRICITY"],
                    "arg_of_pericenter": row["ARG_OF_PERICENTER"],
                    "mean_anomaly": row["MEAN_ANOMALY"],
                    "mean_motion": row["MEAN_MOTION"],
                    "epoch": row["EPOCH"],
                    "ingestion_time": ingestion_time,
                    "run_id": run_id,
                }
            )

        except Exception as e:
            norad = row.get("NORAD_CAT_ID", row.get("norad_cat_id", "UNKNOWN"))
            context.log.warning(
                f"Falha ao calcular posição do NORAD {norad}: {e}"
            )

    context.log.info(f"{len(positions)} posições calculadas")
    return positions


@op
def write_satellites_position_gp_to_minio(context, rows):
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

    local_path = f"/tmp/satellites_position_gp_{file_id}.parquet"
    s3_key = (
        f"stage/satellites_position_gp/run_date={run_date}/"
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
    context.log.info(f"Arquivo de posição GP gravado no MinIO: {s3_path}")
    return s3_path


@op(required_resource_keys={"trino"})
def register_position_gp_parquet_in_iceberg(context, parquet_path):
    if not parquet_path:
        context.log.info("Nenhum parquet de posição GP para registrar.")
        return

    conn = context.resources.trino
    cur = conn.cursor()

    location = parquet_path.rsplit("/", 1)[0]

    query = f"""
    ALTER TABLE satellites_position_gp
    EXECUTE add_files(
        location => '{location}',
        format => 'PARQUET'
    )
    """

    cur.execute(query)
    context.log.info(f"Parquet de posição GP registrado no Iceberg: {location}")