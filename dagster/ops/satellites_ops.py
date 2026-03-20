from dagster import op
import os
import uuid
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from datetime import datetime, timezone

TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"


def parse_tle(text: str):
    lines = [line for line in text.splitlines() if line.strip()]
    rows = []

    run_id = str(uuid.uuid4())
    ingestion_time = datetime.now(timezone.utc)

    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            continue

        name = lines[i].strip()
        l1 = lines[i + 1]
        l2 = lines[i + 2]

        try:
            norad_id = int(l1[2:7].strip())
            classification = l1[7].strip()
            international_designator = l1[9:17].strip()
            epoch = l1[18:32].strip()

            mean_motion_dot_raw = l1[33:43].strip()
            mean_motion_dot = float(mean_motion_dot_raw) if mean_motion_dot_raw else None

            mean_motion_ddot = l1[44:52].strip()
            bstar = l1[53:61].strip()

            ephemeris_type_raw = l1[62:63].strip()
            ephemeris_type = int(ephemeris_type_raw) if ephemeris_type_raw else None

            element_number_raw = l1[64:68].strip()
            element_number = int(element_number_raw) if element_number_raw else None

            inclination = float(l2[8:16].strip())
            raan = float(l2[17:25].strip())
            eccentricity = float("0." + l2[26:33].strip())
            argument_of_perigee = float(l2[34:42].strip())
            mean_anomaly = float(l2[43:51].strip())
            mean_motion = float(l2[52:63].strip())

        except Exception:
            continue

        rows.append(
    {
        "name": name,
        "norad_id": norad_id,
        "classification": classification,
        "international_designator": international_designator,
        "epoch": epoch,
        "mean_motion_dot": mean_motion_dot,
        "mean_motion_ddot": mean_motion_ddot,
        "bstar": bstar,
        "ephemeris_type": ephemeris_type,
        "element_number": element_number,
        "inclination": inclination,
        "raan": raan,
        "eccentricity": eccentricity,
        "argument_of_perigee": argument_of_perigee,
        "mean_anomaly": mean_anomaly,
        "mean_motion": mean_motion,
        "tle_line1": l1,
        "tle_line2": l2,
        "ingestion_time": ingestion_time,
        "run_id": run_id,
    }
)

    return rows


@op
def fetch_satellites():
    response = requests.get(TLE_URL, timeout=60)
    response.raise_for_status()
    return parse_tle(response.text)


@op
def write_satellites_to_minio(context, rows):
    if not rows:
        context.log.info("Nenhuma linha para gravar.")
        return None

    s3_endpoint = os.environ["S3_ENDPOINT"]
    s3_access_key = os.environ["S3_ACCESS_KEY"]
    s3_secret_key = os.environ["S3_SECRET_KEY"]
    s3_bucket = os.environ["S3_BUCKET"]

    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_folder = str(uuid.uuid4())
    file_id = str(uuid.uuid4())

    local_path = f"/tmp/satellites_tle_{file_id}.parquet"
    s3_key = f"stage/satellites_tle/run_date={run_date}/run_id={run_folder}/part-{file_id}.parquet"

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
    context.log.info(f"Arquivo gravado no MinIO: {s3_path}")

    return s3_path


@op(required_resource_keys={"trino"})
def register_parquet_in_iceberg(context, parquet_path):
    if not parquet_path:
        context.log.info("Nenhum parquet para registrar no Iceberg.")
        return

    conn = context.resources.trino
    cur = conn.cursor()

    location = parquet_path.rsplit("/", 1)[0]

    query = f"""
    ALTER TABLE satellites_tle
    EXECUTE add_files(
        location => '{location}',
        format => 'PARQUET'
    )
    """

    cur.execute(query)
    context.log.info(f"Parquet registrado no Iceberg a partir de: {location}")