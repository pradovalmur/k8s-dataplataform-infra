from dagster import Definitions

from jobs.satellites_catalog_job import ingest_satellites_catalog
from jobs.satellites_gp_raw_job import ingest_space_track_gp_raw
from jobs.satellites_position_gp_job import ingest_satellites_position_gp

from resources.trino import trino_resource

from schedules.satellites_catalog_schedule import daily_satellites_catalog_schedule
from schedules.satellites_gp_raw_schedule import hourly_space_track_gp_raw_schedule
from schedules.satellites_position_gp_schedule import hourly_satellites_position_gp_schedule

defs = Definitions(
    jobs=[
        ingest_satellites_catalog,
        ingest_space_track_gp_raw,
        ingest_satellites_position_gp,
    ],
    schedules=[
        daily_satellites_catalog_schedule,
        hourly_space_track_gp_raw_schedule,
        hourly_satellites_position_gp_schedule,
    ],
    resources={
        "trino": trino_resource,
    },
)