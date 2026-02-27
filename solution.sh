#!/usr/bin/env bash
set -euo pipefail

echo "Fixing readiness probe..."

kubectl patch deploy bleater-minio-ui -n bleater \
--type='json' \
-p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/ready"},
  {"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/port","value":9001}
]'

echo "Waiting for rollout..."
kubectl rollout status deploy/bleater-minio-ui -n bleater