from dagster import ScheduleDefinition
from jobs.satellites_gp_raw_job import ingest_space_track_gp_raw

hourly_space_track_gp_raw_schedule = ScheduleDefinition(
    job=ingest_space_track_gp_raw,
    cron_schedule="17 * * * *",
    execution_timezone="UTC",
)