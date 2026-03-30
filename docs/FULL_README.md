# Click Arena — DevSecOps Pipeline Project

## Table of Contents

1. [Overview](#overview)
2. [What is this project?](#what-is-this-project)
3. [Tech Stack and Tools](#tech-stack-and-tools)
4. [Project Structure](#project-structure)
5. [The Application](#the-application)
6. [Containerization](#containerization)
7. [Azure Infrastructure](#azure-infrastructure)
8. [Infrastructure as Code with Terraform](#infrastructure-as-code-with-terraform)
9. [CI/CD Pipeline with Jenkins](#cicd-pipeline-with-jenkins)
10. [Post-Deploy Verification with Ansible](#post-deploy-verification-with-ansible)
11. [Security Scanning](#security-scanning)
12. [Cloudflare Worker — Edge Middleware](#cloudflare-worker--edge-middleware)
13. [What's Next](#whats-next)

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
- Edge middleware with Cloudflare Workers
- Cost-conscious Azure architecture (scales to zero when idle)

---

## What is this project?

This project builds a full DevSecOps pipeline around a simple multiplayer game. Every tool in the stack has a real job — not a tutorial exercise. The game gives the pipeline something concrete to build, scan, deploy, and monitor.

The pipeline covers the full lifecycle: code is scanned for vulnerabilities before it ships, packaged into a container, pushed to a private registry, deployed to Azure via infrastructure defined as code, and verified post-deploy. Security scanning runs automatically at every stage. A Cloudflare Worker sits at the edge adding HTTP security headers and protecting API routes.

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
| Cloudflare Worker | Edge middleware — security headers, API key validation, cron audit |
| SonarQube | Static code analysis / SAST |
| Snyk | Dependency vulnerability scanning / SCA |
| Trivy | Container image security scanning |
| OWASP ZAP | Dynamic application security testing / DAST — coming |
| Azure Monitor + Grafana | Metrics and monitoring — coming |
| Git / GitHub | Version control |
| Azure CLI | Resource management and scripting |

---

## Project Structure

```
click-arena/
├── app/
│   ├── server.py              # Entry point — initializes Flask and SocketIO
│   ├── game.py                # WebSocket event handlers and target spawner
│   ├── routes.py              # HTTP routes (/, /health, /stats)
│   ├── state.py               # Shared in-memory game state
│   ├── requirements.txt       # Python dependencies
│   └── templates/
│       └── index.html         # Game frontend — single HTML file
├── cloudflare/
│   └── click-arena-headers/
│       ├── src/
│       │   └── index.js       # Cloudflare Worker — middleware logic
│       └── wrangler.jsonc     # Worker config — name, routes, cron schedule
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

The server is split across four files to keep concerns separate:

- `state.py` holds shared in-memory game state — connected players, active targets, and the last 20 chat messages. Everything resets on restart. No database — scores are intentionally ephemeral because the pipeline is the point.
- `game.py` registers all WebSocket event handlers: connect, join, click_target, chat_message, disconnect. A background thread keeps exactly three targets on screen at all times.
- `routes.py` handles three HTTP routes: `/` serves the game page, `/health` returns a JSON status object used by Azure and Jenkins, `/stats` returns live game metrics and is protected by the Cloudflare Worker API key check.
- `server.py` is the entry point — initializes Flask and SocketIO, registers routes and events, starts the background target spawner.

### Running Locally

```bash
git clone https://github.com/VanshBhardwaj1945/Click-Arena-DevSecOps.git
cd Click-Arena-DevSecOps

python3 -m venv .venv
source .venv/bin/activate
pip3 install -r app/requirements.txt
python3 -m app.server
# Visit http://localhost:8080
```

> *Python 3.14 introduced a breaking change with eventlet. The server uses `async_mode='threading'` instead, which works across all Python versions. Port 8080 is used locally to avoid macOS AirPlay Receiver which occupies port 5000.*

---

## Containerization

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 5000
CMD ["python3", "-m", "app.server"]
```

Dependencies are copied and installed before application code — Docker caches each layer, so unchanged dependencies don't trigger a reinstall on every build.

```bash
docker build -t click-arena .
docker run -p 8080:5000 click-arena
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

All resources in East US. Container Apps scales to zero when idle — hosting cost is effectively zero. Only ongoing cost is ACR at approximately $5/month.

### Manual Setup

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

---

## Infrastructure as Code with Terraform

**Source:** [`terraform/`](./terraform/)

All Azure infrastructure declared in version-controlled `.tf` files. `terraform destroy` tears everything down cleanly. `terraform apply` rebuilds it identically.

### Resources Managed

| Resource Type | Terraform Label | Azure Name |
|---|---|---|
| `azurerm_resource_group` | `mainRG` | `click-arena-rg` |
| `azurerm_container_registry` | `mainACR` | `clickarenaregistry` |
| `azurerm_log_analytics_workspace` | `mainLA` | `click-arena-logs` |
| `azurerm_container_app_environment` | `mainCAE` | `click-arena-env` |
| `azurerm_container_app` | `main` | `click-arena` |

### Key Issues Resolved During Import

| Issue | Resolution |
|---|---|
| `logs_destination` argument not valid | Removed — not supported in `azurerm` 3.x |
| Container App Environment forced replacement | Existing environment had no Log Analytics workspace — Azure requires recreation to add one |
| Environment deletion hung 20+ minutes | Used `terraform state rm` to remove stuck resource, reapplied cleanly |
| Inconsistent resource labels | Standardized all labels before applying |

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## CI/CD Pipeline with Jenkins

<figure>
  <img src="screenshots/02-Jenkins-Build-Success.png" width="400">
  <figcaption>Build history showing failures during debugging, ending in a successful green build</figcaption>
</figure>

Jenkins runs self-hosted in a Docker container. The pipeline executes locally and deploys to Azure via a Service Principal. Nothing runs on GitHub's servers.

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

# Tools installed inside container after first launch
docker exec -it jenkins apt-get install -y docker.io ansible trivy
docker exec -it jenkins bash -c "curl -sL https://aka.ms/InstallAzureCLIDeb | bash"
docker exec -it jenkins bash -c "npm install -g snyk"
docker exec -it jenkins bash -c "
    wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip -P /tmp &&
    unzip /tmp/sonar-scanner-cli-5.0.1.3006-linux.zip -d /opt &&
    ln -s /opt/sonar-scanner-5.0.1.3006-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner
"
docker exec jenkins git config --global --add safe.directory '*'
```

### Pipeline Stages

| Stage | What it does |
|---|---|
| Checkout | Pulls latest code from GitHub |
| SAST — SonarQube | Scans Python source code for bugs and security hotspots |
| SCA — Snyk | Scans dependencies for known CVEs |
| Build Docker Image | Builds and tags container image with Jenkins build number |
| Container Scan — Trivy | Scans built image for OS-level CVEs before push |
| Push to ACR | Pushes tagged image to Azure Container Registry |
| Deploy to Container App | Updates running container via Azure CLI Service Principal |
| Ansible Verification | Structured post-deploy health checks against live URL |
| Smoke Test | Final `/health` endpoint confirmation |

### Credentials

| Credential ID | Purpose |
|---|---|
| `ACR_PASSWORD` | Azure Container Registry password |
| `ACR_USERNAME` | Azure Container Registry username |
| `AZURE_CREDENTIALS` | Service Principal JSON for `az login` |
| `SONAR_TOKEN` | SonarQube analysis token |
| `SNYK_TOKEN` | Snyk API token |

### Key Issues Resolved

| Issue | Resolution |
|---|---|
| Docker permission denied on every restart | Running as root (`-u root`) gives permanent socket access |
| `az login` state not persisting | Installed Azure CLI directly in Jenkins — login persists in same shell session |
| Git safe directory error after container recreation | `git config --global --add safe.directory '*'` inside container |

---

## Post-Deploy Verification with Ansible

**Source:** [`ansible/playbook.yml`](./ansible/playbook.yml)

Ansible runs a structured verification playbook after every deploy before the pipeline is marked green. It verifies response content, response time, and specific JSON fields — deeper than the smoke test which only checks HTTP 200.

### Verification Tasks

| Task | Module | What it checks |
|---|---|---|
| Wait for app to be ready | `wait_for` | Port 443 accepts connections within 60 seconds |
| Check health endpoint | `uri` | GET `/health` returns HTTP 200 |
| Verify health response content | `assert` | Response JSON contains `status: ok` |
| Verify response time | `assert` | Response time under 5000ms |
| Verify expected fields | `assert` | Response contains `players` and `targets` fields |
| Print health response | `debug` | Prints full response to pipeline logs |

<figure>
  <img src="screenshots/03-ansible-build.png" width="600">
  <figcaption>All 7 Ansible tasks passing in the Jenkins pipeline</figcaption>
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

SonarQube reads Python source code without running it, checking for bugs and security vulnerabilities. Runs as a local Docker container (`localhost:9000`). `host.docker.internal` is used as the SonarQube URL from Jenkins because `localhost` inside a Docker container refers to the container itself, not the host machine.

<img src="docs/screenshots/03-Initial-SonarQube-Scan.png" width="500">

**First scan findings:**

| Finding | Severity | Resolution |
|---|---|---|
| CSRF — `cors_allowed_origins="*"` | High | Fixed: restricted to known Azure and localhost URLs |
| Weak PRNG — `random.randint()` in `game.py` x3 | Medium | Marked Safe — game target position generation, no security implication |
| Missing resource integrity on CDN script | Low | Accepted |
| Missing `lang` attribute on `<html>` | Bug | Fixed: added `lang="en"` |

The pseudorandom number generator findings are Security Hotspots — SonarQube flags them for human review, not as confirmed vulnerabilities. After reviewing and documenting the reasoning, they were marked Safe in the SonarQube dashboard. This is the correct professional workflow: not every hotspot requires a code change.

### SCA — Snyk

Snyk scans `requirements.txt` for known CVEs in Flask, Flask-SocketIO, and their transitive dependencies. This is the class of vulnerability exemplified by Log4Shell — a trusted, widely-used library containing a critical flaw that affects every application using it regardless of how clean the application code is.

Runs on every build with `--skip-unresolved` and reports without blocking the pipeline. The Snyk pip scanner requires Python in the PATH to resolve the full dependency tree — in the Jenkins container environment this caused consistent scan failures despite successful authentication. A known CLI/environment compatibility issue documented here for transparency.

### Container Scan — Trivy

Trivy scans the built Docker image for OS-level CVEs in the Debian packages baked into `python:3.11-slim`. Distinct from Snyk which scans Python dependencies — Trivy operates at the image layer level.

```
trivy image \
    --exit-code 0 \
    --severity HIGH,CRITICAL \
    --format table \
    click-arena:${IMAGE_TAG}
```

CVEs in base images are expected. `python:3.11-slim` is Debian-based and will always have some OS-level findings. The correct response is to track them and update the base image periodically — not zero-tolerance blocking. `--exit-code 0` reports findings without failing the pipeline.

---

## Cloudflare Worker — Edge Middleware

**Source:** [`cloudflare/click-arena-headers/src/index.js`](./cloudflare/click-arena-headers/src/index.js)

A Cloudflare Worker deployed to `clickarena.vanshbhardwaj.com` intercepts every HTTP request before it reaches Azure. Deployed and managed via Wrangler CLI, version controlled alongside the rest of the project.

### Architecture

```
Browser
  ↓
Cloudflare Edge (DDoS protection, SSL termination)
  ↓
Cloudflare Worker (runs on every request)
  ├── Checks path — public or protected?
  ├── Validates X-API-Key header on protected routes
  ├── Forwards allowed requests to Azure
  └── Injects security headers on every response
  ↓
Azure Container App
```

### How it works

The Worker has three responsibilities:

**1. API key middleware**

Every request path is checked against a public paths list. Public routes (`/`, `/health`, `/favicon.ico`) pass through without validation. All other routes require a valid `X-API-Key` header. Invalid or missing keys return a 401 immediately — the Azure app never sees the request.

```javascript
const isPublic = PUBLIC_PATHS.includes(path) || path.startsWith('/socket.io');

if (isPublic) {
    return forwardToAzure(azureUrl, req);
} else {
    const apiKey = req.headers.get('X-API-Key');
    if (VALID_API_KEYS.has(apiKey)) {
        stats.allowed += 1;
        return forwardToAzure(azureUrl, req);
    } else {
        stats.blocked += 1;
        return new Response("Blocked - invalid API key", { status: 401 });
    }
}
```

A `Set` is used for `VALID_API_KEYS` rather than an array — O(1) lookup vs O(n) for array iteration. At request volume this difference matters.

**2. Security header injection**

HTTP responses from `fetch()` are immutable. To add headers, the response is cloned into a new mutable `Response` object, headers are added, and the modified copy is returned to the browser.

```javascript
async function forwardToAzure(azureUrl, req) {
    const azureResponse = await fetch(azureUrl, {
        method: req.method,
        headers: req.headers,
        body: req.method !== 'GET' ? req.body : null
    });

    const newResponse = new Response(azureResponse.body, azureResponse);

    newResponse.headers.set('X-Frame-Options', 'DENY');
    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    newResponse.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    newResponse.headers.set('Content-Security-Policy',
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'");

    return newResponse;
}
```

These headers tell the browser how to behave when rendering the page — blocking clickjacking, preventing MIME sniffing, restricting script sources, and disabling unused hardware features. They protect the user, not the server.

**3. Scheduled audit cron job**

A cron trigger fires every 5 minutes and logs request statistics to Cloudflare's observability dashboard.

```javascript
async scheduled(event, env, ctx) {
    console.log('[AUDIT] ' + new Date().toISOString());
    console.log('[AUDIT] Allowed: ' + stats.allowed);
    console.log('[AUDIT] Blocked: ' + stats.blocked);
    console.log('[AUDIT] Total Requests: ' + stats.total);

    let blockRate;
    if (stats.total > 0) {
        blockRate = ((stats.blocked / stats.total) * 100).toFixed(1);
    } else {
        blockRate = 0;
    }
    console.log('[AUDIT] Block Rate: ' + blockRate + '%');
}
```

### Deployment

```bash
cd cloudflare/click-arena-headers
wrangler deploy
```

### Verification

```bash
# Security headers present on every response
curl -sI https://clickarena.vanshbhardwaj.com/health
# → x-frame-options: DENY
# → content-security-policy: default-src 'self'...
# → x-content-type-options: nosniff
# → referrer-policy: strict-origin-when-cross-origin
# → permissions-policy: camera=(), microphone=(), geolocation=()

# Protected route blocked without key
curl https://clickarena.vanshbhardwaj.com/stats
# → 401 Blocked - invalid API key

# Protected route accessible with valid key
curl -H "X-API-Key: sk_arena_dev_123" https://clickarena.vanshbhardwaj.com/stats
# → {"active_players":0,"messages_sent":5,"status":"live"}
```

### Key Issues Resolved

| Issue | Resolution |
|---|---|
| SSL error 525 on custom domain | Cloudflare SSL mode was set to Full Strict — Azure cert not verified by Cloudflare. Changed to Full |
| ERR_TOO_MANY_REDIRECTS | Flexible SSL mode causes infinite redirect loop — Azure redirects HTTP to HTTPS which loops back through Cloudflare. Changed to Full |
| Worker returning fake strings instead of game | Worker intercepted traffic before forwarding logic was written — detached route from domain until Worker was complete |
| WebSocket connections broken through proxy | Flask-SocketIO WebSocket upgrade incompatible with Cloudflare Worker proxying — game served directly from Azure URL, Worker handles HTTP API routes |
| Response headers immutable | HTTP responses from `fetch()` are read-only — cloned into new `Response` object before adding headers |

---

## What's Next

- **OWASP ZAP** — dynamic scan against the live Azure URL, attacking the running application like a real adversary. Expected to find missing headers (already fixed by the Worker), XSS vectors via the chat input, and clickjacking vulnerabilities
- **Azure Monitor + Grafana** — live dashboard showing active WebSocket connections, request latency, and container memory usage. Log Analytics Workspace is already collecting data — Grafana connects to it as a data source
- **Gitleaks** — scan git history for accidentally committed secrets. The hardcoded `SECRET_KEY` in `server.py` is a real finding waiting to be caught

---