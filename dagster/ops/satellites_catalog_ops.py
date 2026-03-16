from dagster import op
import os
import uuid
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from datetime import datetime, timezone

SATCAT_URL = "https://celestrak.org/pub/satcat.csv"


def parse_date(value):
    if pd.isna(value) or not str(value).strip():
        return None
    return pd.to_datetime(value).date()


def parse_float(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)


def parse_int(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return int(value)


@op
def fetch_satellites_catalog():
    response = requests.get(SATCAT_URL, timeout=120)
    response.raise_for_status()

    run_id = str(uuid.uuid4())
    ingestion_time = datetime.now(timezone.utc)

    df = pd.read_csv(pd.io.common.StringIO(response.text))

    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "object_name": str(row.get("OBJECT_NAME", "")).strip() or None,
                "object_id": str(row.get("OBJECT_ID", "")).strip() or None,
                "norad_cat_id": parse_int(row.get("NORAD_CAT_ID")),
                "object_type": str(row.get("OBJECT_TYPE", "")).strip() or None,
                "ops_status_code": str(row.get("OPS_STATUS_CODE", "")).strip() or None,
                "owner": str(row.get("OWNER", "")).strip() or None,
                "launch_date": parse_date(row.get("LAUNCH_DATE")),
                "launch_site": str(row.get("LAUNCH_SITE", "")).strip() or None,
                "decay_date": parse_date(row.get("DECAY_DATE")),
                "period": parse_float(row.get("PERIOD")),
                "inclination": parse_float(row.get("INCLINATION")),
                "apogee": parse_int(row.get("APOGEE")),
                "perigee": parse_int(row.get("PERIGEE")),
                "rcs": str(row.get("RCS", "")).strip() or None,
                "data_status_code": str(row.get("DATA_STATUS_CODE", "")).strip() or None,
                "orbit_center": str(row.get("ORBIT_CENTER", "")).strip() or None,
                "orbit_type": str(row.get("ORBIT_TYPE", "")).strip() or None,
                "ingestion_time": ingestion_time,
                "run_id": run_id,
            }
        )

    return rows


@op
def write_satellites_catalog_to_minio(context, rows):
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

    local_path = f"/tmp/satellites_catalog_{file_id}.parquet"
    s3_key = f"stage/satellites_catalog/run_date={run_date}/run_id={run_folder}/part-{file_id}.parquet"

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
def register_catalog_parquet_in_iceberg(context, parquet_path):
    if not parquet_path:
        context.log.info("Nenhum parquet para registrar no Iceberg.")
        return

    conn = context.resources.trino
    cur = conn.cursor()

    location = parquet_path.rsplit("/", 1)[0]

    query = f"""
    ALTER TABLE satellites_catalog
    EXECUTE add_files(
        location => '{location}',
        format => 'PARQUET'
    )
    """

    cur.execute(query)
    context.log.info(f"Parquet registrado no Iceberg a partir de: {location}")