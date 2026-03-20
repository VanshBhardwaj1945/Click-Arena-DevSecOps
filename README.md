# Click Arena — DevSecOps Pipeline on Azure

> A real-time multiplayer browser game used as a vehicle for building and demonstrating a production-grade DevSecOps pipeline on Azure.
> The game is intentionally simple. **The infrastructure is the point.**

**[▶ Play the game](https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io)** &nbsp;|&nbsp; **[📖 Full documentation](docs/FULL_README.md)**

---

## What this demonstrates

A complete DevSecOps pipeline — from local development to a live, monitored, security-scanned deployment on Azure. Every tool has a real job. Nothing is a tutorial exercise.

```
Code Push → Jenkins → Docker Build → ACR → Azure Container Apps → Ansible Verify → Live
```

---

## Stack

| Layer | Tools |
|---|---|
| **Application** | Python 3.11, Flask, Flask-SocketIO |
| **Containerization** | Docker, Azure Container Registry |
| **Hosting** | Azure Container Apps (serverless, scales to zero) |
| **Infrastructure** | Terraform, Azure CLI |
| **CI/CD** | Jenkins (self-hosted, pipeline as code) |
| **Config & Verify** | Ansible |
| **SAST** | SonarQube *(coming)* |
| **Dependency Scan** | Snyk *(coming)* |
| **Container Scan** | Trivy *(coming)* |
| **DAST** | OWASP ZAP *(coming)* |
| **Monitoring** | Azure Monitor + Grafana *(coming)* |
| **Secrets** | Azure Key Vault *(coming)* |

---

## Pipeline

<img src="docs/screenshots/02-Jenkins-Build-Success.png" width="379">

The pipeline runs automatically on every push. Each stage must pass before the next begins.

| Stage | Status |
|---|---|
| Checkout from GitHub | ✅ Complete |
| Build Docker image | ✅ Complete |
| Push to Azure Container Registry | ✅ Complete |
| Deploy to Azure Container Apps | ✅ Complete |
| Ansible post-deploy verification | ✅ Complete |
| Smoke test (`/health` endpoint) | ✅ Complete |
| SonarQube SAST scan | 🔧 Coming |
| Snyk dependency scan | 🔧 Coming |
| Trivy container scan | 🔧 Coming |
| OWASP ZAP DAST scan | 🔧 Coming |

---

## Ansible Verification

After every deploy, Ansible runs a structured verification playbook against the live Azure URL before the pipeline is marked green.

<img src="docs/screenshots/03-ansible-build.png" width="600">

```
TASK [Wait for app to be ready] ........... ok
TASK [Check health endpoint] .............. ok
TASK [Verify health response content] ..... ok — "App is healthy and responding correctly"
TASK [Verify response time is acceptable] . ok — "Response time is acceptable"
TASK [Verify health response has expected fields] ok — "Health response contains all expected fields"
TASK [Print health response] .............. ok — {'players': 0, 'status': 'ok', 'targets': 3}

localhost: ok=7  changed=0  unreachable=0  failed=0  skipped=0
```

---

## Azure Infrastructure

All infrastructure is defined as code in Terraform — no clicking through the portal.

```
Azure Subscription
└── Resource Group (click-arena-rg)
    ├── Container Registry       — stores Docker images
    ├── Log Analytics Workspace  — collects container logs
    ├── Container Apps Env       — shared hosting platform
    └── Container App            — live game server (public HTTPS URL)
```

```bash
cd terraform
terraform init
terraform apply   # rebuilds the entire stack from scratch
```

---

## Quick Start

```bash
git clone https://github.com/VanshBhardwaj1945/Click-Arena-DevSecOps.git
cd Click-Arena-DevSecOps

python3 -m venv .venv && source .venv/bin/activate
pip3 install -r app/requirements.txt
python3 -m app.server

# Visit http://localhost:8080
# Open a second tab and join with a different name to test multiplayer
```

**With Docker:**

```bash
docker build -t click-arena .
docker run -p 8080:5000 click-arena
```

---

## About this project

Built as a hands-on learning project while studying for the **AZ-104** exam. The goal was to build something real — not follow a tutorial — and document every decision, blocker, and fix along the way.

**[Read the full documentation →](docs/FULL_README.md)**

---