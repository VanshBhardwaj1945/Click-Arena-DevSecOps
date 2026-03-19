# Click Arena — DevSecOps Pipeline Project

## Table of Contents

1. [Overview](#overview)
2. [What is this project?](#what-is-this-project)
3. [Tech Stack and Tools](#tech-stack-and-tools)
4. [Project Structure](#project-structure)
5. [The Application](#the-application)
   - [Flask-SocketIO Game Server](#flask-socketio-game-server)
   - [Real-Time Chat](#real-time-chat)
   - [Running Locally](#running-locally)
6. [Containerization](#containerization)
   - [Dockerfile](#dockerfile)
   - [Building and Running with Docker](#building-and-running-with-docker)
7. [Azure Infrastructure](#azure-infrastructure)
   - [Resources Created](#resources-created)
   - [Manual Setup](#manual-setup)
   - [Pushing to Azure Container Registry](#pushing-to-azure-container-registry)
   - [Deploying to Azure Container Apps](#deploying-to-azure-container-apps)
8. [Infrastructure as Code with Terraform](#infrastructure-as-code-with-terraform)
   - [Why Terraform](#why-terraform)
   - [Terraform Project Structure](#terraform-project-structure)
   - [Resources Managed](#resources-managed)
   - [Importing Existing Infrastructure](#importing-existing-infrastructure)
   - [Applying the Configuration](#applying-the-configuration)
9. [What's Next](#whats-next)

---

## Overview

Click Arena is a real-time multiplayer browser game built as a vehicle for learning and demonstrating a full DevSecOps pipeline on Azure. Players click targets that appear on screen and compete on a live leaderboard, with real-time chat between players.

**The game is intentionally simple. The infrastructure is the point.**

**Live demo:** [https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io](https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io)

**Skills demonstrated so far:**

- Real-time multiplayer with Python, Flask, and WebSockets
- Containerization with Docker
- Private image storage with Azure Container Registry
- Serverless container hosting with Azure Container Apps
- Infrastructure as Code with Terraform
- Cost-conscious Azure architecture (scales to zero when idle)

---

## What is this project?

This project builds a full DevSecOps pipeline around a simple multiplayer game. Every tool in the stack has a real job — not a tutorial exercise. The game gives the pipeline something concrete to build, scan, deploy, and monitor.

The pipeline covers the full lifecycle: code is scanned for vulnerabilities before it ships, packaged into a container, pushed to a private registry, deployed to Azure via infrastructure defined as code, and monitored in production. Security scanning runs automatically at every stage — static code analysis, dependency scanning, container scanning, and dynamic testing against the live URL.

This is being built and documented as a hands-on learning project while studying for the AZ-104 exam.

---

## Tech Stack and Tools

| Tool / Technology | Purpose |
|---|---|
| Python 3.11 | Application language |
| Flask | Web framework and HTTP routing |
| Flask-SocketIO | Real-time WebSocket communication |
| Docker | Containerization |
| Azure Container Registry | Private Docker image storage |
| Azure Container Apps | Serverless container hosting |
| Azure Log Analytics Workspace | Log collection for Container Apps |
| Terraform | Infrastructure as Code |
| Ansible | Post-deploy configuration and smoke tests *(coming)* |
| Jenkins | CI/CD pipeline orchestration *(coming)* |
| SonarQube | Static code analysis / SAST *(coming)* |
| Snyk | Dependency vulnerability scanning / SCA *(coming)* |
| Trivy | Container image security scanning *(coming)* |
| OWASP ZAP | Dynamic application security testing / DAST *(coming)* |
| Azure Monitor + Grafana | Metrics and monitoring *(coming)* |
| Azure Key Vault | Secret management *(coming)* |
| Git / GitHub | Version control |
| Azure CLI | Resource management and scripting |

---

## Project Structure

```
click-arena/
├── app/
│   ├── server.py              # Entry point — initializes Flask and SocketIO
│   ├── game.py                # WebSocket event handlers and target spawner
│   ├── routes.py              # HTTP routes (/, /health)
│   ├── state.py               # Shared in-memory game state
│   ├── requirements.txt       # Python dependencies
│   └── templates/
│       └── index.html         # Game frontend — single HTML file
├── terraform/
│   ├── main.tf                # Azure resource definitions
│   ├── providers.tf           # Terraform and AzureRM provider configuration
│   ├── variables.tf           # Input variable declarations
│   └── outputs.tf             # Outputs printed after apply
├── ansible/
│   └── playbook.yml           # Post-deploy configuration (coming)
├── jenkins/
│   └── Jenkinsfile            # CI/CD pipeline definition (coming)
├── Dockerfile                 # Container build instructions
├── .gitignore
└── README.md
```

---

## The Application

### Flask-SocketIO Game Server

The server is split across four files to keep concerns separate:

- `state.py` holds the shared in-memory game state — a dictionary of connected players and their scores, a list of active targets, and the last 20 chat messages. Everything resets when the server restarts. There is no database — scores are intentionally ephemeral because the pipeline is the point, not persistence.
- `game.py` registers all WebSocket event handlers: connect, join, click_target, chat_message, and disconnect. A background thread runs continuously and keeps exactly three targets on screen at all times.
- `routes.py` handles two HTTP routes: `/` serves the game page and `/health` returns a JSON status object that Azure and Jenkins use to confirm the app is alive.
- `server.py` is the entry point — it initializes Flask and SocketIO, registers the routes and events from the other modules, starts the background target spawner thread, and starts the server.

### Real-Time Chat

Players can send messages while playing. Messages appear in real time across all connected browser tabs using WebSocket broadcasts. Join and leave events are broadcast as system messages. The server keeps the last 20 messages in memory and sends chat history to new players on connect.

Chat input is intentionally left with minimal server-side sanitization — this is a deliberate choice to give OWASP ZAP and SonarQube something real to find during security scanning later in the pipeline.

### Running Locally

```bash
# Clone the repo
git clone https://github.com/VanshBhardwaj1945/Click-Arena-DevSecOps.git
cd Click-Arena-DevSecOps

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r app/requirements.txt

# Run the server
python3 -m app.server
# Visit http://localhost:8080
```

Open a second tab and join with a different name to test the multiplayer and chat.

> *Python 3.14 introduced a breaking change with eventlet — the async library Flask-SocketIO commonly uses. Rather than pinning to an older Python version, the server was configured to use threading mode instead (`async_mode='threading'`), which works across all Python versions and requires no additional dependencies. The server port is set to 5000 inside Docker and 8080 locally to avoid a conflict with macOS AirPlay Receiver, which occupies port 5000 by default.*

---

## Containerization

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 5000
CMD ["python3", "-m", "app.server"]
```

`python:3.11-slim` is used rather than the system Python (3.14) because 3.11 is the current stable, widely-supported version that all libraries are tested against. Pinning the base image to a specific version is standard practice — it prevents unexpected breakage when upstream images update.

Dependencies are copied and installed before the application code. Docker caches each layer — if only the code changes, Docker reuses the cached dependency layer and only rebuilds from the code copy step down. On larger projects this saves significant build time.

The server listens on port 5000 inside the container. Port 8080 is used locally to avoid the AirPlay conflict on macOS — inside a Linux container that conflict doesn't exist.

### Building and Running with Docker

```bash
# Build the image
docker build -t click-arena .

# Run locally (maps container port 5000 to local port 8080)
docker run -p 8080:5000 click-arena
# Visit http://localhost:8080

# Check running containers
docker ps

# Check built images
docker images
```

---

## Azure Infrastructure

### Resources Created

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `click-arena-rg` | Logical container for all project resources |
| Container Registry | `clickarenaregistry` | Private storage for Docker images |
| Log Analytics Workspace | `click-arena-logs` | Log collection for Container Apps environment |
| Container Apps Environment | `click-arena-env` | Shared hosting platform for Container Apps |
| Container App | `click-arena` | The running game server with public ingress |

All resources are in the `East US` region.

### Manual Setup

All resources were initially created manually using the Azure CLI to understand what each resource does before codifying them in Terraform. This mirrors the workflow from my Cloud Resume Challenge — build it manually first, then bring it under IaC.

```bash
# Create resource group
az group create --name click-arena-rg --location eastus

# Create container registry
az acr create \
  --resource-group click-arena-rg \
  --name clickarenaregistry \
  --sku Basic \
  --admin-enabled true

# Create Container Apps environment
az containerapp env create \
  --name click-arena-env \
  --resource-group click-arena-rg \
  --location eastus

# Deploy the container app
az containerapp create \
  --name click-arena \
  --resource-group click-arena-rg \
  --environment click-arena-env \
  --image clickarenaregistry.azurecr.io/click-arena:v1 \
  --registry-server clickarenaregistry.azurecr.io \
  --target-port 5000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3
```

### Pushing to Azure Container Registry

```bash
# Authenticate Docker to ACR (tokens expire — re-run if push fails)
az acr login --name clickarenaregistry

# Tag the local image with the full ACR address
docker tag click-arena clickarenaregistry.azurecr.io/click-arena:v3

# Push to ACR
docker push clickarenaregistry.azurecr.io/click-arena:v3

# Confirm the image arrived
az acr repository show-tags \
  --name clickarenaregistry \
  --repository click-arena \
  --output table
```

### Deploying to Azure Container Apps

```bash
# Update the running container app to a new image version
az containerapp update \
  --name click-arena \
  --resource-group click-arena-rg \
  --image clickarenaregistry.azurecr.io/click-arena:v3
```

Container Apps scales to zero replicas when idle and back up when traffic arrives. At this scale the hosting cost is essentially zero — charges are per request, not per hour. The only ongoing cost is the Container Registry at approximately $5/month for the Basic tier.

> *The first deployment failed with a port mismatch — the container was listening on port 8080 (the local development port) but Azure expected 5000. The fix was straightforward: set the server port to 5000 in the Dockerfile entrypoint since AirPlay Receiver is a macOS-only concern that doesn't exist inside a Linux container.*

---

## Infrastructure as Code with Terraform

After building everything manually, all Azure infrastructure was codified in Terraform. Every resource is now declared in version-controlled `.tf` files, giving a complete and reproducible picture of the environment.

**Source:** [`terraform/`](./terraform/)

### Why Terraform

Clicking through the portal leaves no auditable record of how things were configured and makes it difficult to reproduce the environment. Terraform solves this by declaring infrastructure in code that can be committed to Git and applied consistently. It also forces a deeper understanding of each resource — you have to know what every argument does rather than accepting portal defaults.

The practical benefit: `terraform destroy` tears everything down cleanly, `terraform apply` rebuilds it identically. For a project kept live for employers to see, the `.tf` files also serve as self-documenting infrastructure — they answer "how was this built?" without needing separate documentation.

### Terraform Project Structure

```
terraform/
├── main.tf        # All Azure resource definitions
├── providers.tf   # Terraform version and AzureRM provider configuration
├── variables.tf   # Reusable input variables (location, resource group name)
└── outputs.tf     # Values printed after apply (game URL, ACR login server)
```

### Resources Managed

| Resource Type | Terraform Label | Azure Name |
|---|---|---|
| `azurerm_resource_group` | `mainRG` | `click-arena-rg` |
| `azurerm_container_registry` | `mainACR` | `clickarenaregistry` |
| `azurerm_log_analytics_workspace` | `mainLA` | `click-arena-logs` |
| `azurerm_container_app_environment` | `mainCAE` | `click-arena-env` |
| `azurerm_container_app` | `main` | `click-arena` |

### Importing Existing Infrastructure

Since all resources were originally created through the Azure CLI, `terraform import` was used to bring each one into Terraform state without recreating anything.

```bash
terraform import azurerm_resource_group.mainRG \
  /subscriptions/YOUR_SUB_ID/resourceGroups/click-arena-rg

terraform import azurerm_container_registry.mainACR \
  /subscriptions/YOUR_SUB_ID/resourceGroups/click-arena-rg/providers/Microsoft.ContainerRegistry/registries/clickarenaregistry

terraform import azurerm_container_app_environment.mainCAE \
  /subscriptions/YOUR_SUB_ID/resourceGroups/click-arena-rg/providers/Microsoft.App/managedEnvironments/click-arena-env

terraform import azurerm_container_app.main \
  /subscriptions/YOUR_SUB_ID/resourceGroups/click-arena-rg/providers/Microsoft.App/containerApps/click-arena
```

**Key issues resolved during import:**

| Issue | Resolution |
|---|---|
| `logs_destination` argument not valid | Removed — not supported in `azurerm` 3.x; the Log Analytics workspace ID alone is sufficient to connect them |
| Container App Environment forced replacement | The existing environment had no Log Analytics workspace attached. Azure does not allow adding one to an existing environment — it must be recreated. Accepted the replacement and let Terraform destroy and recreate it |
| Environment deletion hung for 20+ minutes | Azure deleted the resource but never sent the confirmation back to Terraform. Used `terraform state rm` to remove the stuck resource from state, then reapplied cleanly |
| Inconsistent resource reference names | Initial code used mixed labels (`main`, `mainRG`, `mainACR`) causing reference errors. Standardized all resource labels before applying |

> *Importing existing infrastructure is significantly harder than writing Terraform for new resources. The process exposed invisible configuration — provider-level argument differences, Azure defaults that don't match Terraform defaults, and API timeout behaviour that looks like a hang but isn't. Working through each issue gave a much deeper understanding of how Container Apps infrastructure is actually structured under the hood.*

### Applying the Configuration

```bash
cd terraform

# Download the AzureRM provider
terraform init

# Preview what will be created or changed (safe — makes no changes)
terraform plan

# Apply the configuration
terraform apply
```

After a successful apply, Terraform prints the configured outputs:

```
Outputs:

acr_login_server = "clickarenaregistry.azurecr.io"
game_url         = "https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io"
```

These outputs are also available programmatically — Jenkins will use this later to know what URL to pass to OWASP ZAP for dynamic scanning:

```bash
terraform output -raw game_url
```

---

## What's Next

The following pipeline stages are being added:

- **Jenkins** — local CI/CD pipeline that triggers on every GitHub push, runs all security scans, builds and pushes the Docker image, and deploys to Azure via Terraform
- **SonarQube** — static analysis of the Python code, expected to flag the hardcoded `SECRET_KEY` and insufficient chat input sanitization
- **Snyk** — dependency scanning of Flask and Flask-SocketIO for known CVEs
- **Trivy** — container image scanning for OS-level vulnerabilities in the `python:3.11-slim` base image
- **Ansible** — post-deploy playbook that hits the `/health` endpoint and confirms the deployment succeeded before marking the pipeline green
- **OWASP ZAP** — dynamic scan against the live Azure URL, expected to find missing security headers and test the chat input for XSS
- **Azure Monitor + Grafana** — live dashboard showing active WebSocket connections, request latency, and container memory usage
- **Azure Key Vault** — secrets management for the Snyk token and ACR credentials used in the Jenkins pipeline

---