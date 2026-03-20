from dagster import Definitions

from jobs.satellites_job import ingest_satellites
from jobs.satellites_catalog_job import ingest_satellites_catalog
from jobs.satellites_position_job import ingest_satellites_position

from resources.trino import trino_resource

from schedules.satellites_schedule import hourly_satellites_schedule
from schedules.satellites_catalog_schedule import daily_satellites_catalog_schedule
from schedules.satellites_position_schedule import hourly_satellites_position_schedule

defs = Definitions(
    jobs=[
        ingest_satellites,
        ingest_satellites_catalog,
        ingest_satellites_position,
    ],
    schedules=[
        hourly_satellites_schedule,
        daily_satellites_catalog_schedule,
        hourly_satellites_position_schedule,
    ],
    resources={
        "trino": trino_resource,
    },
)