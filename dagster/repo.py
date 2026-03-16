from dagster import Definitions

from jobs.satellites_job import ingest_satellites
from jobs.satellites_catalog_job import ingest_satellites_catalog
from resources.trino import trino_resource
from schedules.satellites_schedule import hourly_satellites_schedule
from schedules.satellites_catalog_schedule import daily_satellites_catalog_schedule

defs = Definitions(
    jobs=[
        ingest_satellites,
        ingest_satellites_catalog,
    ],
    schedules=[
        hourly_satellites_schedule,
        daily_satellites_catalog_schedule,
    ],
    resources={
        "trino": trino_resource,
    },
)