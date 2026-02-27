#!/usr/bin/env python3

"""
Nebula Grader — Broken Readiness Probe Task

This grader validates that the agent correctly repairs a Kubernetes
Deployment suffering from readiness probe configuration drift.

The grader performs FIVE independent validations:

1. Readiness probe path is corrected to `/ready`
2. Readiness probe port is corrected to `9001`
3. Deployment resource was NOT deleted/recreated (UID preserved)
4. Deployment successfully becomes Ready
5. Service endpoints exist (pods became Ready)

Score = passed_checks / total_checks

All checks query live Kubernetes cluster state using kubectl.
"""

import subprocess
import time
from apex_arena._types import GradingResult


# -----------------------------------------------------------
# Utility: Run shell command safely
# -----------------------------------------------------------

def run(cmd: str):
    """Execute shell command and return stdout safely."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return ""


# -----------------------------------------------------------
# Wait for deployment readiness (handles rollout timing)
# -----------------------------------------------------------

def wait_for_ready():
    """
    Wait until deployment reports ready replicas.

    Kubernetes rollouts are asynchronous, so we retry multiple
    times to avoid flaky grading caused by timing delays.
    """
    for _ in range(10):
        ready = run(
            "kubectl get deployment bleater-minio-ui -n bleater "
            "-o jsonpath='{.status.readyReplicas}'"
        )
        if ready and ready != "0":
            return True
        time.sleep(3)
    return False


# -----------------------------------------------------------
# Main grading entrypoint
# -----------------------------------------------------------

def grade(transcript: str) -> GradingResult:
    """
    Perform grading checks against live Kubernetes state.

    Each check validates one required behavior described
    in the task specification.
    """

    checks = {}

    # -------------------------------------------------------
    # Check 1 — Readiness probe path corrected
    # -------------------------------------------------------
    try:
        path = run(
            "kubectl get deployment bleater-minio-ui -n bleater "
            "-o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.path}'"
        )
        checks["probe_path_correct"] = path == "/ready"
    except Exception:
        checks["probe_path_correct"] = False

    # -------------------------------------------------------
    # Check 2 — Readiness probe port corrected
    # -------------------------------------------------------
    try:
        port = run(
            "kubectl get deployment bleater-minio-ui -n bleater "
            "-o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.port}'"
        )
        checks["probe_port_correct"] = port == "9001"
    except Exception:
        checks["probe_port_correct"] = False

    # -------------------------------------------------------
    # Check 3 — Deployment NOT recreated (UID anti-cheat)
    # -------------------------------------------------------
    try:
        original_uid = ""
        try:
            with open("/tmp/bleater-deploy-uid") as f:
                original_uid = f.read().strip()
        except Exception:
            pass

        current_uid = run(
            "kubectl get deployment bleater-minio-ui -n bleater "
            "-o jsonpath='{.metadata.uid}'"
        )

        checks["resource_not_recreated"] = (
            original_uid != "" and original_uid == current_uid
        )
    except Exception:
        checks["resource_not_recreated"] = False

    # -------------------------------------------------------
    # Check 4 — Deployment becomes Ready
    # -------------------------------------------------------
    checks["deployment_ready"] = wait_for_ready()

    # -------------------------------------------------------
    # Check 5 — Service endpoints restored
    # -------------------------------------------------------
    try:
        endpoints = run(
            "kubectl get endpoints bleater-minio-ui -n bleater "
            "-o jsonpath='{.subsets}'"
        )
        checks["service_has_endpoints"] = endpoints != ""
    except Exception:
        checks["service_has_endpoints"] = False

    # -------------------------------------------------------
    # Score calculation
    # -------------------------------------------------------
    total = len(checks)
    passed = sum(checks.values())
    score = passed / total

    feedback = " | ".join(
        [f"{k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    )

    return GradingResult(
        score=score,
        subscores=checks,
        weights={k: 1.0 for k in checks},
        feedback=feedback,
    )