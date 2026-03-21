from dagster import op
import os
import uuid
import requests
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone

LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
GP_URL = (
    "https://www.space-track.org/basicspacedata/query/"
    "class/gp/decay_date/null-val/epoch/%3Enow-10/"
    "orderby/norad_cat_id/format/json"
)


def _to_float(value):
    if value in (None, "", "None"):
        return None
    return float(value)


def _to_int(value):
    if value in (None, "", "None"):
        return None
    return int(value)


def _to_ts(value):
    if value in (None, "", "None"):
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


@op
def fetch_space_track_gp_raw(context):
    identity = os.environ["SPACE_TRACK_IDENTITY"]
    password = os.environ["SPACE_TRACK_PASSWORD"]

    session = requests.Session()

    login_resp = session.post(
        LOGIN_URL,
        data={"identity": identity, "password": password},
        timeout=60,
    )
    login_resp.raise_for_status()

    resp = session.get(GP_URL, timeout=180)
    resp.raise_for_status()

    data = resp.json()

    run_id = str(uuid.uuid4())
    ingestion_time = datetime.now(timezone.utc)

    rows = []
    for row in data:
        rows.append(
            {
                "object_name": row.get("OBJECT_NAME"),
                "norad_cat_id": _to_int(row.get("NORAD_CAT_ID")),
                "object_id": row.get("OBJECT_ID"),
                "epoch": _to_ts(row.get("EPOCH")),
                "mean_motion": _to_float(row.get("MEAN_MOTION")),
                "eccentricity": _to_float(row.get("ECCENTRICITY")),
                "inclination": _to_float(row.get("INCLINATION")),
                "ra_of_asc_node": _to_float(row.get("RA_OF_ASC_NODE")),
                "arg_of_pericenter": _to_float(row.get("ARG_OF_PERICENTER")),
                "mean_anomaly": _to_float(row.get("MEAN_ANOMALY")),
                "ephemeris_type": _to_int(row.get("EPHEMERIS_TYPE")),
                "bstar": _to_float(row.get("BSTAR")),
                "mean_motion_dot": _to_float(row.get("MEAN_MOTION_DOT")),
                "mean_motion_ddot": _to_float(row.get("MEAN_MOTION_DDOT")),
                "classification_type": row.get("CLASSIFICATION_TYPE"),
                "element_set_no": _to_int(row.get("ELEMENT_SET_NO")),
                "rev_at_epoch": _to_int(row.get("REV_AT_EPOCH")),
                "decay_date": _to_ts(row.get("DECAY_DATE")),
                "ingestion_time": ingestion_time,
                "run_id": run_id,
            }
        )

    context.log.info(f"{len(rows)} linhas recebidas do Space-Track")
    return rows


@op
def write_space_track_gp_raw_to_minio(context, rows):
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

    local_path = f"/tmp/satellites_gp_raw_{file_id}.parquet"
    s3_key = f"stage/satellites_gp_raw/run_date={run_date}/run_id={run_folder}/part-{file_id}.parquet"

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
def register_space_track_gp_raw_in_iceberg(context, parquet_path):
    if not parquet_path:
        context.log.info("Nenhum parquet para registrar.")
        return

    conn = context.resources.trino
    cur = conn.cursor()

    location = parquet_path.rsplit("/", 1)[0]

    query = f"""
    ALTER TABLE satellites_gp_raw
    EXECUTE add_files(
        location => '{location}',
        format => 'PARQUET'
    )
    """
    cur.execute(query)
    context.log.info(f"Parquet registrado no Iceberg: {location}")