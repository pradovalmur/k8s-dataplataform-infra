from dagster import ScheduleDefinition
from jobs.satellites_position_job import ingest_satellites_position

hourly_satellites_position_schedule = ScheduleDefinition(
    job=ingest_satellites_position,
    cron_schedule="10 * * * *",
    execution_timezone="UTC",
)