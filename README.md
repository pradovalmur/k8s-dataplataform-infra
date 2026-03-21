# Kubernetes Data Platform – Infrastructure

This repository contains a complete data platform running on Kubernetes, focused on building a modern **lakehouse + real-time analytics stack**.

The platform ingests orbital data from Space-Track, stores it in a lakehouse (Iceberg on MinIO), processes it with Dagster, and visualizes it via a custom Dash application.

---

## High-Level Architecture

Data flow overview:

1. Orbital data is ingested from **Space-Track (GP / OMM format)**.
2. **Dagster** orchestrates ingestion and processing pipelines.
3. Raw data is stored in **MinIO (S3-compatible)**.
4. Processed data is written as **Parquet + Iceberg tables**.
5. **Trino** provides SQL access over Iceberg tables.
6. A custom **Dash application** visualizes satellite positions in real time.
7. **Traefik** exposes services via HTTPS.
8. **Rancher** manages the Kubernetes cluster.

---

## Technology Stack

| Layer | Tool |
|---|---|
| Cloud | Hetzner Cloud |
| Container Orchestration | Kubernetes |
| Infrastructure Provisioning | Terraform |
| Cluster Bootstrap | Ansible |
| Ingress Controller | Traefik |
| Object Storage | MinIO |
| Orchestration | Dagster |
| Metadata Databases | PostgreSQL |
| Lakehouse Table Format | Apache Iceberg |
| SQL Query Engine | Trino |
| Visualization | Plotly Dash |
| Cluster Management | Rancher |

---

## Repository Structure

```
k8s-dataplataform-infra/
├── hcloud-k8s-infra/
├── ansible/
├── k8s_resources/
└── README.md
```

---

## Core Data Pipelines

### 1. Satellite Catalog (Daily)
- Source: CelesTrak (satcat)
- Output: `satellites_catalog`
- Purpose: metadata (owner, type, launch site)

### 2. Orbital Elements (Hourly)
- Source: Space-Track (GP / OMM)
- Output: `satellites_gp_raw`
- Purpose: orbital parameters

### 3. Satellite Positions (Hourly)
- Input: `satellites_gp_raw`
- Process: orbit propagation using **Skyfield**
- Output: `satellites_position_gp`
- Purpose: latitude, longitude, altitude, velocity

---

## Data Model

### Core Tables

| Table | Description |
|---|---|
| satellites_catalog | Satellite metadata |
| satellites_gp_raw | Raw orbital elements (Space-Track) |
| satellites_position_gp | Calculated satellite positions |

### Derived Views

| View | Description |
|---|---|
| satellites_catalog_latest | Latest metadata per satellite |
| satellites_latest_position_gp | Latest position per satellite |
| satellites_map_gp | Final dataset used by Dash |

---

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

### 5. Deploy MinIO

```bash
kubectl apply -f k8s_resources/storage/minio.yaml
```

Create buckets:
- analytics
- iceberg

### 6. Deploy Trino + Iceberg

```bash
kubectl apply -f k8s_resources/analytics/trino-iceberg.yaml
```

Validate:

```sql
SHOW SCHEMAS FROM iceberg;
SHOW TABLES FROM iceberg.space;
```

### 7. Deploy Dagster

```bash
kubectl apply -f k8s_resources/orchestration/dagster.yaml
```

### 8. Deploy Dash Application

```bash
kubectl apply -f k8s_resources/apps/dash-satellites.yaml
```

---

## Data Architecture

| Layer | Description |
|---|---|
| raw | Space-Track GP data |
| processed | Satellite positions (Parquet) |
| iceberg | Analytics tables |
| serving | Dash application |

---

## Example Queries

```sql
SELECT *
FROM iceberg.space.satellites_latest_position_gp
LIMIT 10;
```

```sql
SELECT object_type, count(*)
FROM iceberg.space.satellites_map_gp
GROUP BY 1
ORDER BY 2 DESC;
```

---

## Observability (Planned)

- Prometheus
- Grafana
- Loki

---

## Future Improvements

- Orbit visualization in Dash
- Satellite clustering
- Active satellites filtering
- Real-time streaming ingestion
- Alerting (Datadog / Slack)

---

## Disclaimer

This platform is designed for:
- learning
- experimentation
- advanced data engineering practice

Not production-hardened.

---

## Author

Valmur Prado
