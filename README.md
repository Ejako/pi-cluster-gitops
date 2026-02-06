# Pi Cluster GitOps
GitOps repository for my K3s Raspberry Pi cluster running stock
market analysis and ML workloads.
## Structure
- ‘clusters/home/‘ - Home cluster configuration
- ‘infrastructure/‘ - Shared infrastructure (storage, monitoring)
- ‘apps/‘ - Application deployments
## Tools
- **FluxCD** - GitOps operator
- **SOPS** - Secrets encryption
- **Kustomize** - Manifest customization
## Cluster Details
- 3x Raspberry Pi 5 (8GB RAM)
- 1x Jetson Orin Nano Super (To be added)
- K3s v1.28+
- NFS storage provisioner
- Prometheus + Grafana monitoring
