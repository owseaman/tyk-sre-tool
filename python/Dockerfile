# Stage 1: Build Stage
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Runtime Stage
FROM python:3.9-slim

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy application code
COPY --from=builder /app /app

# # Create directory for kubeconfig
# RUN mkdir -p /app/.kube

# # Set environment variable for kubeconfig path
# ENV KUBECONFIG=/app/.kube/config

# Expose the port the app runs on
EXPOSE 8080

# Update CMD to use the mounted config
# CMD ["python", "main.py", "--kubeconfig", "/app/.kube/config", "--address", ":8080"]

# Update CMD to use in-cluster config
CMD ["python", "main.py", "--address", ":8080"]
