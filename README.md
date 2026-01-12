# Kubernetes Data Platform – Infrastructure

This repository contains a complete data platform infrastructure running on Kubernetes, designed for learning, experimentation, and lakehouse pipelines.

## High-Level Architecture

Data flow overview:

1. Raw data (CSV files) is stored in MinIO (S3-compatible).
2. Apache Airflow orchestrates ingestion and transformation pipelines.
3. Transformed data is written into Apache Iceberg tables stored in MinIO.
4. Trino queries Iceberg tables using SQL.
5. Metabase connects to Trino for analytics and dashboards.
6. Traefik exposes services via HTTPS.
7. Rancher provides cluster management and observability.

## Technology Stack

| Layer | Tool |
|---|---|
| Cloud | Hetzner Cloud |
| Container Orchestration | Kubernetes |
| Infrastructure Provisioning | Terraform |
| Cluster Bootstrap | Ansible |
| Ingress Controller | Traefik |
| Object Storage | MinIO |
| Orchestration | Apache Airflow (CeleryExecutor) |
| Message Broker | Redis |
| Metadata Databases | PostgreSQL |
| Lakehouse Table Format | Apache Iceberg |
| SQL Query Engine | Trino |
| BI / Analytics | Metabase |
| GitOps (DAGs) | git-sync |

## Repository Structure

```
k8s-dataplataform-infra/
├── hcloud-k8s-infra/
├── ansible/
├── k8s_resources/
└── README.md
```

## Deployment – Step by Step

### 1. Provision Infrastructure (Hetzner)

```bash
cd hcloud-k8s-infra
terraform init
terraform apply
```

### 2. Bootstrap Kubernetes Cluster

```bash
cd ansible
ansible-playbook -i inventory.ini site.yaml
```

### 3. Configure kubectl

```bash
export KUBECONFIG=ansible/kubeconfig/admin.conf
kubectl get nodes
```

### 4. Deploy Ingress (Traefik)

```bash
kubectl apply -f k8s_resources/ingress/traefik.yaml
```

### 5. Deploy Object Storage (MinIO)

```bash
kubectl apply -f k8s_resources/storage/minio.yaml
```

Create buckets:
- analytics
- airflow-logs
- iceberg

### 6. Deploy Apache Airflow

```bash
kubectl apply -f k8s_resources/orchestration/airflow.yaml
```

### 7. Deploy Trino + Iceberg

```bash
kubectl apply -f k8s_resources/analytics/trino-iceberg.yaml
```

Validate:
```sql
SHOW SCHEMAS FROM iceberg;
SHOW TABLES FROM iceberg.analytics;
```

### 8. Deploy Metabase

```bash
kubectl apply -f k8s_resources/analytics/metabase.yaml
```

## Data Architecture

| Layer | Description |
|---|---|
| raw | Original CSV files |
| staging | Cleaned Parquet |
| iceberg | Analytics tables |

## dbt Support

Supports dbt with Trino:

```bash
pip install dbt-core dbt-trino
```

## Observability (Future)

- Prometheus
- Grafana
- Loki

## Troubleshooting

### Airflow logs not visible
- Ensure `airflow-logs` bucket exists
- Check `AIRFLOW_CONN_MINIO_S3`

### Airflow init job immutable error
```bash
kubectl delete job airflow-init -n orchestration
```

## Disclaimer

Optimized for learning and experimentation.

## Author

Valmur Prado
