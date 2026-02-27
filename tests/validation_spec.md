# Broken Readiness Probe

## Problem

The Bleater platform team reports that the MinIO UI service is returning intermittent **503 Service Unavailable** errors.

Investigation shows that the Kubernetes Deployment exists and pods are running, but the Service has **no ready endpoints**.

A recent configuration drift introduced an incorrect readiness probe configuration.

Your task is to repair the deployment **without recreating it**.

---

## Environment Initialization

The environment is automatically prepared before execution:

- Namespace `bleater` is created.
- Deployment `bleater-minio-ui` is deployed with an incorrect readiness probe.
- Service `bleater-minio-ui` exposes the deployment.
- The original Deployment UID is saved for validation.

Pods start successfully but never become **Ready**.

---

## Drifted Configuration

| Field | Current Value |
|------|---------------|
| Readiness Path | `/healthz` |
| Readiness Port | `8080` |

Because of this drift:

- Pods remain Running but Not Ready
- Service has zero endpoints
- Rolling updates never complete
- Traffic returns 503 errors

---

## Required Fix

Repair the existing Deployment:

Name: `bleater-minio-ui`  
Namespace: `bleater`

Update the readiness probe so that:

| Field | Expected Value |
|------|----------------|
| Path | `/ready` |
| Port | `9001` |

---

## Constraints

You MUST:

- Patch the existing Deployment
- Preserve the Deployment UID
- Allow rollout to complete naturally

You MUST NOT:

- Delete the Deployment
- Recreate resources
- Modify unrelated objects

---

## Success Conditions

The task is complete when:

1. Readiness probe path equals `/ready`
2. Readiness probe port equals `9001`
3. Deployment UID remains unchanged
4. Deployment reports ready replicas
5. Service endpoints are restored

---

## Validation

Validation reads live Kubernetes cluster state using `kubectl`.

Checks include:

- Probe configuration correctness
- Resource preservation (anti-cheat UID check)
- Deployment readiness
- Service endpoint recovery

---

## Goal

Diagnose and repair Kubernetes configuration drift by safely patching a live Deployment.