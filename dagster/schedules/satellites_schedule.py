from dagster import ScheduleDefinition
from jobs.satellites_job import ingest_satellites

hourly_satellites_schedule = ScheduleDefinition(
    job=ingest_satellites,
    cron_schedule="0 * * * *",  # executa a cada hora
    execution_timezone="UTC",
)