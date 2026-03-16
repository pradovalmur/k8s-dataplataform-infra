FROM dagster/dagster-k8s:1.12.18

WORKDIR /opt/dagster/app

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

COPY dagster/ /opt/dagster/app/