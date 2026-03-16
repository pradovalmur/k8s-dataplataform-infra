from dagster import ScheduleDefinition
from jobs.satellites_catalog_job import ingest_satellites_catalog

daily_satellites_catalog_schedule = ScheduleDefinition(
    job=ingest_satellites_catalog,
    cron_schedule="0 3 * * *",
    execution_timezone="UTC",
)