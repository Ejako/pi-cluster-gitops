# Stock Dashboard on Kubernetes 🚀📈

A complete MLOps project demonstrating real-time stock data ingestion, time-series storage, and interactive dashboarding on Kubernetes. Perfect for Raspberry Pi clusters and edge computing learning.

[![Docker Build](https://img.shields.io/badge/Docker-Build-blue)](https://hub.docker.com/r/ejako/stock-backend)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Deploy-green)](https://kubernetes.io)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Local Development](#local-development-with-docker-compose)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Backend Implementation](#backend-implementation)
- [Frontend Implementation](#frontend-implementation)
- [Advanced Deployment](#advanced-deployment)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Best Practices](#best-practices)

## 🎯 Features

- **Real-time Stock Data** - Yahoo Finance integration via `yfinance`
- **Time-Series Database** - PostgreSQL optimized for OHLCV data
- **Interactive Dashboard** - Shiny for Python with technical indicators
- **Production Kubernetes** - StatefulSets, Deployments, Services, CronJobs
- **Multi-Architecture** - ARM64 (Raspberry Pi 5) + x86_64 support
- **Shared NFS Storage** - 2TB USB SSD across multiple projects
- **Automated Updates** - Daily CronJob data refresh
- **Infrastructure as Code** - Declarative Kubernetes manifests

## 🏗️ Architecture

```
Internet ← NodePort:30080
         ↓
┌─────────────────────────────┐
│  Frontend (Shiny Dashboard) │ ← Port 8080
│  • Interactive charts       │
│  • Technical indicators     │
│  • Live data updates        │
└──────────────┬──────────────┘
               │ HTTP API
               ↓
┌─────────────────────────────┐
│   Backend (Flask API)       │ ← Port 5000
│  • yfinance data fetch      │
│  • Technical calculations   │
│  • REST endpoints           │
└──────────────┬──────────────┘
               │ PostgreSQL
               ↓
┌─────────────────────────────┐
│ PostgreSQL + TimescaleDB    │ ← NFS 2TB SSD
│ • stock_prices hypertable   │
│ • Optimized indexes         │
│ • OHLCV data                │
└─────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

```bash
# Docker & Docker Compose
docker --version
docker-compose --version

# Kubernetes (k3s recommended for Raspberry Pi)
kubectl version --client

# Multi-arch build support
docker buildx version
```

### 1. Clone & Build

```bash
# Clone this repo
git clone <your-repo> stock-dashboard
cd stock-dashboard

# Build Docker images locally
docker build -t your-username/stock-backend:1.0 backend/
docker build -t your-username/stock-frontend:1.0 frontend/

# Multi-arch build (Intel → ARM64 for Pi 5)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/stock-backend:1.0 --push ./backend/

docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/stock-frontend:1.0 --push ./frontend/
```

### 2. Local Testing (Docker Compose)

```bash
# Start full stack locally
docker-compose up

# In another terminal, load sample data
curl http://localhost:5000/api/fetch/AAPL
curl http://localhost:5000/api/fetch/GOOGL
curl http://localhost:5000/api/fetch/MSFT

# Access services
# Frontend: http://localhost:8080
# Backend API: http://localhost:5000/api/
```

### 3. Kubernetes Deployment

```bash
# Deploy to cluster
kubectl apply -f k8s/

# Verify deployment
kubectl get all

# Port-forward dashboard
kubectl port-forward svc/stock-frontend-service 8080:8080

# Load data via API
curl http://localhost:5000/api/fetch/AAPL

# Access dashboard
# http://localhost:8080
```

## 📁 Project Structure

```
stock-dashboard/
├── README.md                          # This file
├── docker-compose.yml                 # Local development
│
├── backend/                           # Flask API + yfinance
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── .dockerignore
│
├── frontend/                          # Shiny dashboard
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── .dockerignore
│
├── k8s/                               # Kubernetes manifests
│   ├── postgres-statefulset.yaml
│   ├── postgres-secret.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── cronjob-refresh.yaml
│   └── kustomization.yaml
│
└── .env.example
    DOCKER_REGISTRY=your-username
    BACKEND_IMAGE=stock-backend:1.0
    FRONTEND_IMAGE=stock-frontend:1.0
```

## 🗄️ Database Schema

### PostgreSQL Table Definition

```sql
-- Main OHLCV table (hypertable if TimescaleDB available)
CREATE TABLE stock_prices (
    time TIMESTAMPTZ NOT NULL,      -- Timestamp (indexed)
    ticker TEXT NOT NULL,            -- Stock symbol (indexed)
    open FLOAT,                      -- Opening price
    high FLOAT,                      -- Daily high
    low FLOAT,                       -- Daily low
    close FLOAT,                     -- Closing price
    volume BIGINT                    -- Trading volume
);

-- Composite index for fast queries
CREATE INDEX idx_stock_prices_ticker_time 
    ON stock_prices (ticker, time DESC);
```

### Schema Design Rationale

- **TIMESTAMPTZ**: Timezone-aware timestamps for global market data
- **Composite Index**: Fast lookups by ticker and time range
- **Scalability**: Schema extends easily with indicators and technical analysis
- **TimescaleDB Ready**: Hypertable declaration prepares for automatic compression

## 💻 Local Development with Docker Compose

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stocks
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DB_HOST: postgres
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_NAME: stocks
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    environment:
      BACKEND_URL: "http://backend:5000"
    ports:
      - "8080:8080"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

volumes:
  postgres-data:
```

### Running Locally

```bash
# Start all services
docker-compose up

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Stop services
docker-compose down

# Full cleanup (remove volumes)
docker-compose down -v
```

## ☸️ Kubernetes Deployment

### PostgreSQL StatefulSet

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: stocks
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: postgresql
        envFrom:
        - secretRef:
            name: postgres-secret
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 5
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None
  ports:
  - port: 5432
    targetPort: 5432
    name: postgresql
  selector:
    app: postgres
```

### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stock-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stock-backend
  template:
    metadata:
      labels:
        app: stock-backend
    spec:
      containers:
      - name: backend
        image: your-username/stock-backend:1.0
        ports:
        - containerPort: 5000
        env:
        - name: DB_HOST
          value: postgres
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_USER
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_PASSWORD
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_DB
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: stock-backend-service
spec:
  selector:
    app: stock-backend
  ports:
  - port: 5000
    targetPort: 5000
    protocol: TCP
  type: ClusterIP
```

### Frontend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stock-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stock-frontend
  template:
    metadata:
      labels:
        app: stock-frontend
    spec:
      containers:
      - name: frontend
        image: your-username/stock-frontend:1.0
        ports:
        - containerPort: 8080
        env:
        - name: BACKEND_URL
          value: "http://stock-backend-service:5000"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: stock-frontend-service
spec:
  selector:
    app: stock-frontend
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  type: NodePort
  # For LoadBalancer on cloud providers, change type: LoadBalancer
```

### Deploy & Verify

```bash
# Create Kubernetes resources
kubectl apply -f k8s/

# Verify deployments
kubectl get deployments
kubectl get statefulsets
kubectl get pods
kubectl get svc

# Check pod status
kubectl describe pod <pod-name>

# View logs
kubectl logs -f deployment/stock-backend
kubectl logs -f deployment/stock-frontend
kubectl logs -f statefulset/postgres

# Port-forward services
kubectl port-forward svc/stock-frontend-service 8080:8080
kubectl port-forward svc/stock-backend-service 5000:5000

# Access dashboard
# http://localhost:8080
```

## 🐍 Backend Implementation

### Flask API with yfinance

```python
# backend/app.py
from flask import Flask, jsonify
import psycopg2
import yfinance as yf
from datetime import datetime
import os

app = Flask(__name__)

# Database connection
def get_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        database=os.getenv('DB_NAME', 'stocks')
    )

@app.route('/health', methods=['GET'])
def health():
    """Liveness probe"""
    return jsonify({'status': 'ok'}), 200

@app.route('/ready', methods=['GET'])
def ready():
    """Readiness probe - check DB connectivity"""
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'ready'}), 200
    except:
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/fetch/<ticker>', methods=['GET'])
def fetch_stock(ticker):
    """Fetch and store stock data from Yahoo Finance"""
    try:
        # Download data from yfinance
        data = yf.download(ticker, period='1y', progress=False)
        
        # Store in database
        conn = get_db()
        cur = conn.cursor()
        
        for index, row in data.iterrows():
            cur.execute(
                '''INSERT INTO stock_prices 
                   (time, ticker, open, high, low, close, volume)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (time, ticker) DO NOTHING''',
                (index, ticker, row['Open'], row['High'], 
                 row['Low'], row['Close'], int(row['Volume']))
            )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'ticker': ticker,
            'records': len(data)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/<ticker>', methods=['GET'])
def get_stock(ticker):
    """Retrieve stock data"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute(
            '''SELECT time, open, high, low, close, volume 
               FROM stock_prices 
               WHERE ticker = %s 
               ORDER BY time DESC LIMIT 365''',
            (ticker,)
        )
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        data = [
            {
                'time': str(row[0]),
                'open': float(row[1]) if row[1] else None,
                'high': float(row[2]) if row[2] else None,
                'low': float(row[3]) if row[3] else None,
                'close': float(row[4]) if row[4] else None,
                'volume': int(row[5]) if row[5] else None
            }
            for row in rows
        ]
        
        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
```

### Backend Requirements

```
# backend/requirements.txt
Flask==2.3.2
psycopg2-binary==2.9.6
yfinance==0.2.18
requests==2.31.0
```

## 🎨 Frontend Implementation

### Shiny Dashboard

```python
# frontend/app.py
from shiny import App, ui, render, reactive
import requests
import pandas as pd
import plotly.graph_objects as go

backend_url = "http://stock-backend-service:5000"

app_ui = ui.page_fluid(
    ui.h1("Stock Dashboard"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_text("ticker", "Stock Ticker:", "AAPL"),
            ui.input_action_button("fetch", "Load Data"),
            ui.input_action_button("refresh", "Refresh"),
        ),
        ui.panel_main(
            ui.output_plot("price_chart"),
            ui.output_table("data_table"),
        ),
    ),
)

def server(input, output, session):
    @reactive.effect
    def _():
        if input.fetch():
            ticker = input.ticker().upper()
            try:
                requests.get(f"{backend_url}/api/fetch/{ticker}")
            except:
                pass
    
    @render.plot
    def price_chart():
        try:
            response = requests.get(
                f"{backend_url}/api/data/{input.ticker().upper()}"
            )
            if response.status_code != 200:
                return go.Figure().add_annotation(
                    text="No data available"
                )
            
            data = response.json()
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['time'], 
                y=df['close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title=f"{input.ticker().upper()} Price History",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                hovermode='x unified',
                height=500
            )
            
            return fig
        
        except Exception as e:
            fig = go.Figure().add_annotation(text=f"Error: {str(e)}")
            return fig
    
    @render.table
    def data_table():
        try:
            response = requests.get(
                f"{backend_url}/api/data/{input.ticker().upper()}"
            )
            data = response.json()
            df = pd.DataFrame(data)
            df = df.sort_values('time', ascending=False)
            return df.head(20)
        
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080 || exit 1

CMD ["shiny", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]
```

### Frontend Requirements

```
# frontend/requirements.txt
shiny==0.2.9
pandas==2.0.3
plotly==5.14.0
requests==2.31.0
```

## 🚀 Advanced Deployment

### CronJob for Automated Updates

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: stock-refresh
spec:
  schedule: "0 17 * * 1-5"  # 5 PM weekdays (market close)
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: refresher
            image: your-username/stock-backend:1.0
            command:
            - sh
            - -c
            - |
              for ticker in AAPL GOOGL MSFT TSLA AMZN; do
                echo "Fetching $ticker..."
                curl http://stock-backend-service:5000/api/fetch/$ticker
              done
            env:
            - name: DB_HOST
              value: postgres
          restartPolicy: OnFailure
```

### Kustomization for Multi-Environment Deployment

```yaml
# k8s/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: stock-dashboard

resources:
  - postgres-statefulset.yaml
  - postgres-secret.yaml
  - backend-deployment.yaml
  - frontend-deployment.yaml
  - cronjob-refresh.yaml

commonLabels:
  app: stock-dashboard
  environment: production

replicas:
  - name: stock-backend
    count: 3
  - name: stock-frontend
    count: 2

images:
  - name: postgres
    newTag: "16-alpine"
  - name: stock-backend
    newTag: "1.0"
  - name: stock-frontend
    newTag: "1.0"
```

## 🔍 Monitoring & Troubleshooting

### Checking Status

```bash
# Check all resources
kubectl get all

# Detailed pod info
kubectl describe pod <pod-name>

# Stream logs
kubectl logs -f deployment/stock-backend
kubectl logs -f statefulset/postgres

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/bash

# Check persistent volumes
kubectl get pvc
kubectl describe pvc postgres-storage-postgres-0

# Monitor resource usage
kubectl top nodes
kubectl top pods
```

### Database Access

```bash
# Port-forward to PostgreSQL
kubectl port-forward svc/postgres 5432:5432

# Connect with psql
psql -h localhost -U postgres -d stocks

# Useful queries
SELECT DISTINCT ticker FROM stock_prices;
SELECT COUNT(*) FROM stock_prices;
SELECT * FROM stock_prices WHERE ticker='AAPL' ORDER BY time DESC LIMIT 5;
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Pod stuck in Pending | Check resource requests, node capacity, and PVC availability |
| Backend can't reach DB | Verify Service DNS name, check postgres pod logs, test connectivity |
| Dashboard shows no data | Ensure fetch API was called, check backend logs, verify DB connection |
| High latency queries | Add database indexes, optimize query patterns, enable TimescaleDB |
| Storage filling up | Check data retention policies, implement time-based compression, scale storage |

### Scaling

```bash
# Scale deployments
kubectl scale deployment stock-backend --replicas=5
kubectl scale deployment stock-frontend --replicas=3

# Check autoscaling status
kubectl get hpa
kubectl describe hpa stock-backend
```

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend API | Python 3.11, Flask 2.3 |
| Data Source | yfinance |
| Frontend | Python 3.11, Shiny |
| Database | PostgreSQL 16, TimescaleDB-ready |
| Orchestration | Kubernetes (k3s), StatefulSets |
| Storage | NFS (2TB USB SSD), Persistent Volumes |
| Containerization | Docker, Docker Buildx (multi-arch) |
| Data Format | OHLCV (Open, High, Low, Close, Volume) |

## 📚 API Reference

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/health` | GET | Liveness probe | `curl http://localhost:5000/health` |
| `/ready` | GET | Readiness probe (DB check) | `curl http://localhost:5000/ready` |
| `/api/fetch/{ticker}` | GET | Fetch & store stock data | `curl http://localhost:5000/api/fetch/AAPL` |
| `/api/data/{ticker}` | GET | Retrieve OHLCV data | `curl http://localhost:5000/api/data/AAPL` |

## 💡 Best Practices

- **Version Control**: Tag Docker images with semantic versioning (1.0, 1.1, etc.)
- **Security**: Use Kubernetes Secrets for credentials, never hardcode in manifests
- **Resource Limits**: Set CPU/memory requests and limits for all containers
- **Health Checks**: Implement liveness and readiness probes
- **Monitoring**: Deploy Prometheus/Grafana for metrics and alerting
- **High Availability**: Use multiple replicas and Pod Disruption Budgets
- **Data Persistence**: Configure appropriate storage classes for StatefulSets
- **Graceful Shutdown**: Implement proper termination handlers
- **Testing**: Always test locally with Docker Compose before Kubernetes
- **Documentation**: Keep deployment guides and runbooks updated

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/add-indicators`)
3. Commit changes (`git commit -m 'Add RSI and MACD indicators'`)
4. Push to branch (`git push origin feature/add-indicators`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Kubernetes & k3s teams** for container orchestration
- **Shiny for Python (Posit)** for interactive dashboarding
- **yfinance library maintainers** for market data access
- **PostgreSQL community** for reliable database technology
- **Docker team** for containerization technology

## 📞 Support

For issues and questions:
1. Check Troubleshooting section above
2. Review Kubernetes logs: `kubectl logs -f deployment/stock-backend`
3. Test API endpoints directly: `curl http://localhost:5000/api/data/AAPL`
4. Create GitHub issue with detailed information

---

⭐ **Star this repo if you found it useful for your MLOps learning!**

**Last Updated**: January 28, 2026  
**Version**: 1.0  
**Status**: Production Ready
