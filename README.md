# tyk-sre-assignment

This repository contains the boilerplate projects for the SRE role interview assignments. There are two projects: one for Go and one for Python respectively.

### Go Project

Location: https://github.com/TykTechnologies/tyk-sre-assignment/tree/main/golang

In order to build the project run:
```
go mod tidy & go build
```

To run it against a real Kubernetes API server:
```
./tyk-sre-assignment --kubeconfig '/path/to/your/kube/conf' --address ":8080"
```

To execute unit tests:
```
go test -v
```

### Python Project

Location: https://github.com/TykTechnologies/tyk-sre-assignment/tree/main/python

We suggest using a Python virtual env, e.g.:
```
python3 -m venv .venv
source .venv/bin/activate
```

Make sure to install the dependencies using `pip`:
```
pip3 install -r requirements.txt
```

To run it against a real Kubernetes API server:
```
python3 main.py --kubeconfig '/path/to/your/kube/conf' --address ":8080"
```

To execute unit tests:
```
python3 tests.py -v
```

# Kubernetes SRE Monitoring Tool

## Overview
A tool for monitoring and managing Kubernetes cluster health and security.

## Features
- Deployment health monitoring
- Network policy management
- Kubernetes API server status checking

## Installation

### Using Helm
```bash
helm install sre-tool helm/k8s-sre-tool --namespace monitoring
```

### Local Development
```bash
# Build Docker image
docker build -t k8s-sre-tool:latest .

# Run locally
docker run -p 8080:8080 -v ~/.kube/config:/app/.kube/config:ro k8s-sre-tool:latest
```

## Testing
```bash
python -m pytest tests/
```

