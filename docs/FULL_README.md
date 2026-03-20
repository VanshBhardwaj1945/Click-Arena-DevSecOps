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
11. [What's Next](#whats-next)

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
- CI/CD automation with Jenkins
- Post-deploy verification with Ansible
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

---

## CI/CD Pipeline with Jenkins

Every code push triggers an automated pipeline that builds, pushes, and deploys the application to Azure without any manual steps.

<figure>
  <img src="docs/screenshots/02-Jenkins-Build-Success.png" width="400">
  <figcaption>Build history showing pipeline failures during debugging, ending in a successful green build</figcaption>
</figure>

### Why Jenkins

Jenkins is used here instead of GitHub Actions for two reasons. First, GitHub Actions is already on the resume from the Cloud Resume Challenge — Jenkins is a completely different skill. Second, Jenkins is dominant in enterprise environments — banks, healthcare, and large organisations running their own infrastructure rather than delegating pipeline execution to a third party.

The key difference from GitHub Actions: Jenkins runs on your own infrastructure. The pipeline executes inside a Docker container on the local machine, and deploys out to Azure using a Service Principal. Nothing runs on GitHub's servers.

### Setup

Jenkins runs as a Docker container locally:

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

Running as root (`-u root`) ensures persistent Docker socket access — without it the socket permissions reset on every container restart. The Azure CLI and Ansible are installed directly inside the container after first launch:

```bash
# Install Docker CLI
docker exec -it jenkins apt-get install -y docker.io

# Install Azure CLI
docker exec -it jenkins bash -c "curl -sL https://aka.ms/InstallAzureCLIDeb | bash"

# Install Ansible
docker exec -it jenkins apt-get install -y ansible

# Allow git to operate on the workspace directory
docker exec jenkins git config --global --add safe.directory '*'
```

### Pipeline Stages

**Source:** [`jenkins/Jenkinsfile`](./jenkins/Jenkinsfile)

The pipeline is defined as code in the `Jenkinsfile` and runs automatically on a polling schedule (`* * * * *` — every minute).

| Stage | What it does |
|---|---|
| Checkout | Pulls latest code from GitHub |
| Build Docker Image | Builds and tags the container image with the build number |
| Push to ACR | Authenticates to ACR and pushes the tagged image |
| Deploy to Container App | Logs into Azure via Service Principal and updates the running container |
| Ansible — Post Deploy Verification | Runs the Ansible playbook against the live URL |
| Smoke Test | Waits 15 seconds then hits `/health` to confirm the app is alive |

Each build produces a versioned image tag — `v1`, `v2`, `v3` etc — based on the Jenkins build number. This means every deployment is traceable to a specific build.

### Credentials Management

All secrets are stored in Jenkins' built-in credential store and injected into pipeline stages at runtime using `withCredentials`. Nothing sensitive is written in the Jenkinsfile itself.

| Credential ID | Type | Purpose |
|---|---|---|
| `ACR_PASSWORD` | Secret text | Azure Container Registry password |
| `ACR_USERNAME` | Secret text | Azure Container Registry username |
| `AZURE_CREDENTIALS` | Secret text | Service Principal JSON for `az login` |

The Service Principal was created with Contributor scope on the subscription:

```bash
az ad sp create-for-rbac \
  --name "jenkins-click-arena" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUB_ID \
  --sdk-auth
```

### Running the Pipeline

The pipeline polls GitHub every minute and triggers automatically when new commits are detected. It can also be triggered manually from the Jenkins dashboard at `localhost:8090`.

**Key issues resolved during setup:**

| Issue | Resolution |
|---|---|
| Docker permission denied | Running Jenkins as root (`-u root`) gives permanent Docker socket access without needing `chmod` on every restart |
| `az login` state not shared between containers | Each `docker run mcr.microsoft.com/azure-cli` starts a fresh unauthenticated session — fixed by installing Azure CLI directly inside Jenkins so login persists across commands in the same shell |
| Git safe directory error after container recreation | Workspace directory ownership mismatch — fixed with `git config --global --add safe.directory '*'` inside the container |
| Build number auto-increments | `IMAGE_TAG = "v${BUILD_NUMBER}"` uses Jenkins' built-in counter — every build produces a new unique image tag automatically |

> *Recreating the Jenkins container (required when switching to `-u root`) wipes the installed packages but preserves all jobs, credentials, and build history via the `jenkins_home` volume. Docker, Azure CLI, and Ansible need to be reinstalled after any container recreation — this is expected behaviour and a good argument for building a custom Jenkins Docker image with all tools pre-baked in for production use.*

---

## Post-Deploy Verification with Ansible

After Jenkins deploys a new container version, Ansible runs a structured verification playbook against the live Azure URL before the pipeline is marked green.

**Source:** [`ansible/playbook.yml`](./ansible/playbook.yml)

### Why Ansible

The Jenkins smoke test (`curl -f /health`) catches a completely broken deployment — if the app returns anything other than 200 the pipeline fails. But it doesn't verify the response content, check specific fields, or measure response time. Ansible runs a deeper pass with named tasks and structured output, making it clear exactly what was checked and what passed.

The second reason is tool diversity. A curl check in a Jenkinsfile proves shell scripting. An Ansible playbook proves configuration management — a separate skill that appears in almost every DevOps and DevSecOps job description.

Ansible is also agentless — it doesn't require anything installed on the target. It runs locally on Jenkins and makes HTTP requests to the Azure URL over the public internet. No SSH, no remote agent, no additional setup.

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

`hosts: localhost` and `connection: local` mean all tasks run on the Jenkins machine itself — no SSH or remote inventory needed. The `vars` block defines the app URL once so it can be referenced throughout the playbook as `{{ app_url }}`.

### Verification Tasks

| Task | Module | What it checks |
|---|---|---|
| Wait for app to be ready | `wait_for` | Port 443 accepts connections within 60 seconds |
| Check health endpoint | `uri` | GET `/health` returns HTTP 200 |
| Verify health response content | `assert` | Response JSON contains `status: ok` |
| Verify response time | `assert` | Response time under 5000ms |
| Verify expected fields | `assert` | Response contains `players` and `targets` fields |
| Print health response | `debug` | Prints full response to pipeline logs |

The `register: health_response` keyword on the `uri` task saves the full HTTP response — headers, body, status code, elapsed time — into a variable that all subsequent `assert` tasks can inspect.

### Pipeline Output

<figure>
  <img src="docs/screenshots/03-ansible-build.png" width="600">
  <figcaption>Ansible playbook running inside the Jenkins pipeline — all 7 tasks passing with structured output</figcaption>
</figure>

The actual pipeline output from a successful run:

```
TASK [Wait for app to be ready] ........... ok: [localhost]
TASK [Check health endpoint] .............. ok: [localhost]
TASK [Verify health response content] ..... ok: [localhost]
  "msg": "App is healthy and responding correctly"
TASK [Verify response time is acceptable] . ok: [localhost]
  "msg": "Response time is acceptable"
TASK [Verify health response has expected fields] ok: [localhost]
  "msg": "Health response contains all expected fields"
TASK [Print health response] .............. ok: [localhost]
  "msg": "Health response: {'players': 0, 'status': 'ok', 'targets': 3}"

PLAY RECAP
localhost: ok=7  changed=0  unreachable=0  failed=0  skipped=0
```

**Key issue resolved:**

| Issue | Resolution |
|---|---|
| `elapsed.total_seconds()` failed | In this version of Ansible, `elapsed` is an integer (milliseconds) not a Python `timedelta` object — changed the condition to `elapsed < 5000` |

---

## What's Next

The following pipeline stages are being added:

- **SonarQube** — static analysis of the Python code, expected to flag the hardcoded `SECRET_KEY` and insufficient chat input sanitization
- **Snyk** — dependency scanning of Flask and Flask-SocketIO for known CVEs
- **Trivy** — container image scanning for OS-level vulnerabilities in the `python:3.11-slim` base image
- **OWASP ZAP** — dynamic scan against the live Azure URL, expected to find missing security headers and test the chat input for XSS
- **Azure Monitor + Grafana** — live dashboard showing active WebSocket connections, request latency, and container memory usage
- **Azure Key Vault** — secrets management for the Snyk token and ACR credentials used in the Jenkins pipeline

---