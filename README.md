# Pi Cluster GitOps

GitOps repository for my K3s Raspberry Pi cluster running the dividend strategy dashboard.

FluxCD watches this repository and automatically applies any changes to the cluster.
**You never need to run `kubectl apply` manually.**

## Structure

- `clusters/home/` - Home cluster configuration (Flux Kustomizations)
- `clusters/home/namespaces/` - Namespace definitions for all apps
- `infrastructure/` - Shared infrastructure (storage, monitoring)
- `apps/` - Application deployments
- `apps/dividend-dashboard/` - Dividend strategy Shiny dashboard

## Tools

- **FluxCD** - GitOps operator (watches this repo, applies changes to cluster)
- **SOPS** - Secrets encryption (Age key)
- **Kustomize** - Manifest customisation (built into Flux)

## Cluster Details

- 3x Raspberry Pi 5 (8 GB RAM)
- K3s v1.28+
- NFS storage (rpi5-master exports `/data/`)
- Namespace: `dividend-dashboard`

## Daily Workflow

1. Edit YAML files in this repository
2. `git commit -m "description"`
3. `git push origin main`
4. Flux detects the change within 10 minutes (or force: `flux reconcile kustomization flux-system --with-source`)
5. Verify: `kubectl get pods -n dividend-dashboard`

## First-Time Setup

See the GitOps and DevOps Setup Guide for full instructions. High-level steps:

1. Bootstrap Flux: `flux bootstrap github --owner=<you> --repository=pi-cluster-gitops --branch=main --path=./clusters/home`
2. Create age encryption key: `age-keygen -o ~/age.key`
3. Store key in cluster: `kubectl create secret generic sops-age --namespace=flux-system --from-file=age.agekey=$HOME/age.key`
4. Replace `NFS_SERVER_IP` in `apps/dividend-dashboard/storage/pv-pvc.yaml` with rpi5-master LAN IP
5. Replace `YOUR_AGE_PUBLIC_KEY_HERE` in `.sops.yaml` with your age public key
6. Commit and push — Flux applies everything automatically

## Application Source

Application code lives in the separate `dividend-dashboard` repository.
Build and push the ARM64 image: `make build` (from the app repo's `k8s/` directory).
