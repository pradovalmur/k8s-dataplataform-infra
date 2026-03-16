import trino
from dagster import resource

@resource
def trino_resource(_context):
    return trino.dbapi.connect(
        host="trino.analytics.svc.cluster.local",
        port=8080,
        user="dagster",
        catalog="iceberg",
        schema="space",
    )