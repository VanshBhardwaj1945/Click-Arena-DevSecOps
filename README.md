# Click Arena — DevSecOps Pipeline Project

A real-time multiplayer browser game built as a vehicle for learning and 
demonstrating a full DevSecOps pipeline on Azure.

> The game is intentionally simple. The infrastructure is the point.

## Live Demo
🎮 [Play the game](YOUR_AZURE_URL_HERE)

## What This Project Demonstrates

| Area | Tools Used |
|---|---|
| Containerization | Docker, Azure Container Registry |
| Infrastructure as Code | Terraform |
| Configuration Management | Ansible |
| CI/CD Pipeline | Jenkins |
| Static Code Analysis (SAST) | SonarQube |
| Dependency Scanning (SCA) | Snyk |
| Container Security | Trivy |
| Dynamic Testing (DAST) | OWASP ZAP |
| Cloud Hosting | Azure Container Apps |
| Monitoring | Azure Monitor + Grafana |

## Architecture
```
GitHub Push
    ↓
Jenkins Pipeline
    ├── SonarQube (SAST scan)
    ├── Snyk (dependency scan)
    ├── Docker build
    ├── Trivy (container scan)
    └── Deploy to Azure
            ↓
    Azure Container Apps
    (pulled from Azure Container Registry)
            ↓
    Azure Monitor + Grafana
    (metrics and dashboards)
```

## Tech Stack

- **App:** Python, Flask, Flask-SocketIO (real-time WebSockets)
- **Container:** Docker, Azure Container Registry (Basic tier)
- **Hosting:** Azure Container Apps (scales to zero when idle)
- **IaC:** Terraform — all Azure resources defined as code
- **Config:** Ansible — post-deploy configuration and smoke tests
- **CI/CD:** Jenkins running locally, deploying to Azure
- **Security:** SonarQube + Snyk + Trivy + OWASP ZAP in pipeline

## Pipeline Flow

1. Code pushed to GitHub
2. Jenkins detects the push and triggers the pipeline
3. SonarQube scans Python code for vulnerabilities
4. Snyk checks dependencies for known CVEs
5. Docker builds the container image
6. Trivy scans the image for OS-level vulnerabilities
7. Image pushed to Azure Container Registry
8. Deployed to Azure Container Apps
9. OWASP ZAP runs dynamic scan against live URL
10. Azure Monitor collects metrics, visible in Grafana

## Project Structure
```
click-arena/
├── app/
│   ├── server.py          # Flask-SocketIO game server
│   └── requirements.txt   # Python dependencies
├── terraform/
│   ├── main.tf            # Azure infrastructure definition
│   ├── variables.tf       # Reusable config values
│   └── outputs.tf         # Prints URLs and resource names
├── ansible/
│   └── playbook.yml       # Post-deploy configuration
├── jenkins/
│   └── Jenkinsfile        # CI/CD pipeline definition
├── Dockerfile             # Container build instructions
└── README.md
```

## How to Run Locally
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/click-arena.git
cd click-arena

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r app/requirements.txt

# Run the game
python3 app/server.py
# Visit http://localhost:8080
```

## How to Run with Docker
```bash
docker build -t click-arena .
docker run -p 8080:5000 click-arena
# Visit http://localhost:8080
```

## Status
🚧 Pipeline being built out — check back for updates

---
Built as a hands-on DevSecOps learning project.