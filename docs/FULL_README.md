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
9. [CI/CD Pipeline with Jenkins](#cicd-pipeline-with-jenkins)
   - [Why Jenkins](#why-jenkins)
   - [Setup](#setup)
   - [Pipeline Stages](#pipeline-stages)
   - [Credentials Management](#credentials-management)
   - [Running the Pipeline](#running-the-pipeline)
10. [Post-Deploy Verification with Ansible](#post-deploy-verification-with-ansible)
    - [Why Ansible](#why-ansible)
    - [Playbook Structure](#playbook-structure)
    - [Verification Tasks](#verification-tasks)
    - [Pipeline Output](#pipeline-output)
11. [Security Scanning](#security-scanning)
    - [SAST — SonarQube](#sast--sonarqube)
    - [SCA — Snyk](#sca--snyk)
    - [Container Scan — Trivy](#container-scan--trivy)
12. [What's Next](#whats-next)

---

## Overview

Click Arena is a real-time multiplayer browser game built as a vehicle for learning and demonstrating a full DevSecOps pipeline on Azure. Players click targets that appear on screen and compete on a live leaderboard, with real-time chat between players.

**The game is intentionally simple. The infrastructure is the point.**

**Live demo:** [https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io](https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io)

**Skills demonstrated:**

- Real-time multiplayer with Python, Flask, and WebSockets
- Containerization with Docker
- Private image storage with Azure Container Registry
- Serverless container hosting with Azure Container Apps
- Infrastructure as Code with Terraform
- CI/CD automation with Jenkins
- Post-deploy verification with Ansible
- Static code analysis with SonarQube
- Dependency vulnerability scanning with Snyk
- Container image scanning with Trivy
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
| Jenkins | CI/CD pipeline orchestration |
| Ansible | Post-deploy verification |
| SonarQube | Static code analysis / SAST |
| Snyk | Dependency vulnerability scanning / SCA |
| Trivy | Container image security scanning |
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
│   └── playbook.yml           # Post-deploy verification playbook
├── jenkins/
│   └── Jenkinsfile            # CI/CD pipeline definition
├── docs/
│   └── screenshots/           # Pipeline and deployment screenshots
├── Dockerfile                 # Container build instructions
├── .dockerignore              # Files excluded from Docker build context
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

Chat input is intentionally left with minimal server-side sanitization — this gave SonarQube and OWASP ZAP something real to find during security scanning.

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

### Building and Running with Docker

```bash
docker build -t click-arena .
docker run -p 8080:5000 click-arena
# Visit http://localhost:8080
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

All resources were initially created manually using the Azure CLI to understand what each resource does before codifying them in Terraform.

```bash
az group create --name click-arena-rg --location eastus

az acr create \
  --resource-group click-arena-rg \
  --name clickarenaregistry \
  --sku Basic \
  --admin-enabled true

az containerapp env create \
  --name click-arena-env \
  --resource-group click-arena-rg \
  --location eastus

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
az acr login --name clickarenaregistry
docker tag click-arena clickarenaregistry.azurecr.io/click-arena:v3
docker push clickarenaregistry.azurecr.io/click-arena:v3
```

### Deploying to Azure Container Apps

```bash
az containerapp update \
  --name click-arena \
  --resource-group click-arena-rg \
  --image clickarenaregistry.azurecr.io/click-arena:v3
```

Container Apps scales to zero when idle — hosting cost is essentially zero at this scale. The only ongoing cost is ACR at approximately $5/month.

> *The first deployment failed with a port mismatch — the container was listening on port 8080 but Azure expected 5000. Fixed by setting the server port to 5000 in the Dockerfile entrypoint since AirPlay Receiver is a macOS-only concern that doesn't exist inside a Linux container.*

---

## Infrastructure as Code with Terraform

**Source:** [`terraform/`](./terraform/)

### Why Terraform

Clicking through the portal leaves no auditable record of how things were configured and makes it difficult to reproduce the environment. Terraform solves this by declaring infrastructure in code that can be committed to Git and applied consistently.

### Terraform Project Structure

```
terraform/
├── main.tf        # All Azure resource definitions
├── providers.tf   # Terraform version and AzureRM provider configuration
├── variables.tf   # Reusable input variables
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

**Key issues resolved:**

| Issue | Resolution |
|---|---|
| `logs_destination` argument not valid | Removed — not supported in `azurerm` 3.x |
| Container App Environment forced replacement | Existing environment had no Log Analytics workspace — must be recreated to add one. Accepted the replacement |
| Environment deletion hung 20+ minutes | Used `terraform state rm` to remove stuck resource, reapplied cleanly |
| Inconsistent resource labels | Standardized all references to `mainRG`, `mainACR`, `mainCAE` |

> *Importing existing infrastructure exposed invisible configuration — portal defaults that don't match Terraform defaults, provider bugs, and API timeout behaviour that looks like a hang. Working through each issue gave a much deeper understanding of how Container Apps infrastructure is actually structured.*

### Applying the Configuration

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

```
Outputs:

acr_login_server = "clickarenaregistry.azurecr.io"
game_url         = "https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io"
```

---

## CI/CD Pipeline with Jenkins

<figure>
  <img src="screenshots/02-Jenkins-Build-Success.png" width="400">
  <figcaption>Build history showing pipeline failures during debugging, ending in a successful green build</figcaption>
</figure>

### Why Jenkins

Jenkins is used instead of GitHub Actions because GitHub Actions is already on the resume from the Cloud Resume Challenge. Jenkins is a completely different skill — self-hosted, dominant in enterprise environments where pipelines cannot run on third-party infrastructure.

### Setup

```bash
docker run -d \
  --name jenkins \
  -u root \
  --restart unless-stopped \
  -p 8090:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

Tools installed inside the container after first launch: Docker CLI, Azure CLI, Ansible, Snyk (via npm), Trivy, SonarQube Scanner. Running as root ensures persistent Docker socket access without permission resets on restart.

### Pipeline Stages

| Stage | What it does |
|---|---|
| Checkout | Pulls latest code from GitHub |
| SAST — SonarQube | Scans Python source code for bugs and security hotspots |
| SCA — Snyk | Scans dependencies for known CVEs |
| Build Docker Image | Builds and tags container image with build number |
| Container Scan — Trivy | Scans built image for OS-level CVEs |
| Push to ACR | Pushes tagged image to Azure Container Registry |
| Deploy to Container App | Updates running container via Azure CLI Service Principal |
| Ansible Verification | Structured post-deploy health checks |
| Smoke Test | Final `/health` endpoint confirmation |

### Credentials Management

| Credential ID | Purpose |
|---|---|
| `ACR_PASSWORD` | Azure Container Registry password |
| `ACR_USERNAME` | Azure Container Registry username |
| `AZURE_CREDENTIALS` | Service Principal JSON for `az login` |
| `SONAR_TOKEN` | SonarQube analysis token |
| `SNYK_TOKEN` | Snyk API token |

**Key issues resolved:**

| Issue | Resolution |
|---|---|
| Docker permission denied | Running as root (`-u root`) gives permanent socket access |
| `az login` state not shared between containers | Installed Azure CLI directly in Jenkins — login persists in same shell session |
| Git safe directory error | `git config --global --add safe.directory '*'` inside container |

---

## Post-Deploy Verification with Ansible

**Source:** [`ansible/playbook.yml`](./ansible/playbook.yml)

### Why Ansible

The smoke test catches a completely broken deployment. Ansible runs a deeper structured pass — verifying response content, response time, and specific JSON fields — with named tasks and clear pass/fail output. It also proves configuration management as a skill, separate from the shell scripting visible in the Jenkinsfile.

### Playbook Structure

```yaml
---
- name: Post-deploy verification for Click Arena
  hosts: localhost
  connection: local
  vars:
    app_url: "https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io"
  tasks:
    - name: Wait for app to be ready
    - name: Check health endpoint
    - name: Verify health response content
    - name: Verify response time is acceptable
    - name: Verify health response has expected fields
    - name: Print health response
```

### Verification Tasks

| Task | Module | What it checks |
|---|---|---|
| Wait for app to be ready | `wait_for` | Port 443 accepts connections within 60 seconds |
| Check health endpoint | `uri` | GET `/health` returns HTTP 200 |
| Verify health response content | `assert` | Response JSON contains `status: ok` |
| Verify response time | `assert` | Response time under 5000ms |
| Verify expected fields | `assert` | Response contains `players` and `targets` fields |
| Print health response | `debug` | Prints full response to pipeline logs |

### Pipeline Output

<figure>
  <img src="screenshots/03-ansible-build.png" width="600">
  <figcaption>Ansible playbook running inside the Jenkins pipeline — all 7 tasks passing</figcaption>
</figure>

```
TASK [Wait for app to be ready] ........... ok: [localhost]
TASK [Check health endpoint] .............. ok: [localhost]
TASK [Verify health response content] ..... ok — "App is healthy and responding correctly"
TASK [Verify response time is acceptable] . ok — "Response time is acceptable"
TASK [Verify health response has expected fields] ok — "Health response contains all expected fields"
TASK [Print health response] .............. ok — {'players': 0, 'status': 'ok', 'targets': 3}

localhost: ok=7  changed=0  unreachable=0  failed=0  skipped=0
```

| Issue | Resolution |
|---|---|
| `elapsed.total_seconds()` failed | `elapsed` is an integer (milliseconds) in this Ansible version — changed condition to `elapsed < 5000` |

---

## Security Scanning

Three security tools run automatically in the Jenkins pipeline before any image reaches Azure. Each scans a different attack surface.

### SAST — SonarQube

SonarQube reads Python source code without running it, looking for bugs and security vulnerabilities. A local SonarQube server (`localhost:9000`) runs in Docker. The scanner runs as a Jenkins pipeline stage before the Docker build.

`host.docker.internal` is used as the SonarQube URL because Jenkins runs inside a Docker container — `localhost` inside a container refers to the container itself, not the Mac host.

**First scan findings:**

| Finding | Severity | Description | Resolution |
|---|---|---|---|
| CSRF hotspot | High | `cors_allowed_origins="*"` on SocketIO | Restricted to known URLs |
| Weak PRNG | Medium | `random.randint()` in `game.py` (×3) | Marked Safe — non-cryptographic game context |
| Missing resource integrity | Low | CDN script tag missing `integrity` attribute | Accepted |
| Missing `lang` attribute | Bug | `<html>` missing `lang="en"` | Fixed directly |

The CSRF fix restricted allowed origins to the Azure URL and localhost:

```python
socketio = SocketIO(app, cors_allowed_origins=[
    "https://click-arena.mangobush-de01fc2e.eastus.azurecontainerapps.io",
    "http://localhost:8080",
    "http://localhost:5000"
], async_mode='threading')
```

The pseudorandom number generator findings were reviewed and marked **Safe** in SonarQube with documented reasoning — `random.randint()` generating game target positions has no security implication. This is the correct professional workflow: not every hotspot requires a code change, some require a human review and a documented decision.

### SCA — Snyk

Snyk scans `requirements.txt` for known CVEs in Flask, Flask-SocketIO, and their transitive dependencies. This catches the class of vulnerability exemplified by Log4Shell — where a trusted, widely-used dependency contains a critical flaw that affects every application using it, regardless of how clean the application code is.

Snyk runs on every build and reports findings without blocking the pipeline (`|| true`). The intent is visibility — knowing what vulnerabilities exist in the dependency tree even if not all can be immediately remediated.

### Container Scan — Trivy

Trivy scans the built Docker image for OS-level CVEs in the Debian packages baked into `python:3.11-slim`. This is distinct from Snyk which scans Python dependencies — Trivy operates at the image layer level, examining everything installed in the base image.

Reports HIGH and CRITICAL findings only. Does not block the pipeline (`--exit-code 0`) — findings are printed to the console on every build, making vulnerability trends visible over time.

> *CVEs in base images are expected and unavoidable. `python:3.11-slim` is Debian-based and will always have some OS-level findings. The correct response is to track them, understand which are exploitable in the application's threat model, and update the base image periodically. Real DevSecOps is about informed risk management, not zero-tolerance blocking.*

---

## What's Next

- **OWASP ZAP** — dynamic scan against the live Azure URL, testing the running application like an attacker would — checking for missing security headers, XSS via the chat input, clickjacking vulnerabilities, and other runtime issues that static scanning cannot detect
- **Azure Monitor + Grafana** — live dashboard showing active WebSocket connections, request latency, and container memory usage
- **Azure Key Vault** — secrets management for the Snyk token, SonarQube token, and ACR credentials, replacing the current Jenkins credential store

---