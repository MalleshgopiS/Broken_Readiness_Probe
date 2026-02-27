#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Setting up Broken Readiness Probe Task"
echo "========================================"

NAMESPACE="bleater"
DEPLOYMENT="bleater-minio-ui"
SERVICE="bleater-minio-ui"

############################################################
# 1. Create Namespace
############################################################

kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

echo "Namespace ready: ${NAMESPACE}"

############################################################
# 2. Create Service
############################################################

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: bleater-minio-ui
  ports:
  - port: 9001
    targetPort: 9001
EOF

echo "Service created"

############################################################
# 3. Create Deployment WITH DRIFTED READINESS PROBE
############################################################

cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bleater-minio-ui
  namespace: bleater
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: bleater-minio-ui
  template:
    metadata:
      labels:
        app: bleater-minio-ui
    spec:
      containers:
      - name: ui
        image: python:3.11-slim
        command:
        - sh
        - -c
        - |
          cat <<'PY' > server.py
          from http.server import BaseHTTPRequestHandler, HTTPServer

          class Handler(BaseHTTPRequestHandler):
              def do_GET(self):
                  if self.path == "/ready":
                      self.send_response(200)
                      self.end_headers()
                      self.wfile.write(b"OK")
                  else:
                      self.send_response(200)
                      self.end_headers()
                      self.wfile.write(b"Hello")

          HTTPServer(("", 9001), Handler).serve_forever()
          PY

          python server.py

        ports:
        - containerPort: 9001

        # -------------------------------
        # INTENTIONAL CONFIGURATION DRIFT
        # -------------------------------
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 2
          periodSeconds: 3
          failureThreshold: 3
EOF

echo "Drifted deployment created"

############################################################
# 4. Wait for Deployment object creation
############################################################

kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=60s || true

############################################################
# 5. Store Original Deployment UID (ANTI-CHEAT)
############################################################

UID_FILE="/tmp/bleater-deploy-uid"

kubectl get deployment ${DEPLOYMENT} \
  -n ${NAMESPACE} \
  -o jsonpath='{.metadata.uid}' > ${UID_FILE}

echo "Original Deployment UID stored:"
cat ${UID_FILE}

############################################################
# 6. Final Status (Debug visibility)
############################################################

echo ""
echo "Current pod status:"
kubectl get pods -n ${NAMESPACE}

echo ""
echo "Setup complete — deployment intentionally broken."
echo "Agent must repair readiness probe WITHOUT recreating resource."
echo "========================================"