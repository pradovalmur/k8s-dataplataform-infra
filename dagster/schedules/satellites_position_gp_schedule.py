from dagster import ScheduleDefinition
from jobs.satellites_position_gp_job import ingest_satellites_position_gp

hourly_satellites_position_gp_schedule = ScheduleDefinition(
    job=ingest_satellites_position_gp,
    cron_schedule="25 * * * *",
    execution_timezone="UTC",
)