"""
End-to-end CloudCart prompt workflow:
input validation → vulnerability assessment → LLM invoke → output validation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import HTTPException

from backend.schemas import UserInputPayload
from backend.services.input_validation import InputValidator, OutputValidator
from backend.services.prompt_manager import PromptManager, PromptVersionManager
from backend.services.vulnerability import assess_injection_risk, build_vulnerability_analysis

version_manager = PromptVersionManager()


def normalize_version(version: str) -> str:
    if version.startswith("v"):
        return version[1:]
    return version


def resolve_prompt_path(version: str) -> str:
    version = (version or "current").strip().lower()
    cloudcart_path = version_manager.get_cloudcart_path()

    if version in {"current", "active", "latest"}:
        success, path_obj, message = version_manager.get_current_version_path()
        if not success or path_obj is None:
            raise HTTPException(
                status_code=404,
                detail=f"Current prompt version not available: {message}",
            )
        return str(path_obj)

    normalized = normalize_version(version)
    candidate = cloudcart_path / f"v{normalized}.yaml"
    if candidate.exists():
        return str(candidate)

    raise HTTPException(status_code=404, detail=f"Prompt version not found: {version}")


def _validation_payload(result) -> Dict[str, Any]:
    return {
        "is_valid": result.is_valid,
        "reason": result.reason,
        "violation_type": result.violation_type,
        "severity": result.severity,
    }


def _blocked(
    reason: str,
    *,
    stage: str,
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
    validation: Optional[Dict[str, Any]] = None,
    vulnerability: Optional[Dict[str, Any]] = None,
    details: Optional[Any] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": "blocked",
        "reason": reason,
        "stage": stage,
    }
    if violation_type is not None:
        payload["violation_type"] = violation_type
    if severity is not None:
        payload["severity"] = severity
    if validation is not None:
        payload["validation"] = validation
    if vulnerability is not None:
        payload["vulnerability"] = vulnerability
    if details is not None:
        payload["details"] = details
    return payload


def _invoke_llm(user_input: str, prompt_version: str) -> Dict[str, Any]:
    prompt_path = resolve_prompt_path(prompt_version)
    manager = PromptManager(prompt_path)

    if not manager.prompt_data:
        return {
            "ok": False,
            "reason": "Failed to load prompt data",
            "prompt_path": prompt_path,
        }

    success, _template, compile_message = manager.compile()
    if not success:
        return {
            "ok": False,
            "reason": f"Prompt compile failed: {compile_message}",
            "prompt_path": prompt_path,
        }

    result = manager.invoke({"user_input": user_input})
    if not result.get("success"):
        errors = result.get("errors") or ["LLM invocation failed"]
        return {
            "ok": False,
            "reason": errors[0],
            "prompt_path": prompt_path,
            "details": result,
        }

    return {
        "ok": True,
        "response": result.get("response"),
        "prompt_path": prompt_path,
        "metadata": manager.get_metadata(),
    }


def execute_submit_workflow(payload: UserInputPayload) -> Dict[str, Any]:
    """Single-endpoint flow used by POST /submit."""
    validation = InputValidator.validate(payload.user_input)
    validation_data = _validation_payload(validation)
    if not validation.is_valid:
        return _blocked(
            validation.reason,
            stage="input_validation",
            violation_type=validation.violation_type,
            severity=validation.severity,
            validation=validation_data,
        )

    risk = assess_injection_risk(payload.user_input)
    vulnerability = build_vulnerability_analysis(
        payload.user_input,
        analyze_safe_template=payload.analyze_safe_template,
        risk=risk,
    )
    if risk["should_block"]:
        return _blocked(
            risk["block_reason"],
            stage="vulnerability_analysis",
            violation_type="prompt_injection_risk",
            severity="critical",
            validation=validation_data,
            vulnerability=vulnerability,
        )

    try:
        invocation = _invoke_llm(payload.user_input, payload.prompt_version)
    except HTTPException:
        raise
    except Exception as exc:
        return _blocked(
            str(exc),
            stage="llm_invocation",
            validation=validation_data,
            vulnerability=vulnerability,
        )

    if not invocation["ok"]:
        return _blocked(
            invocation["reason"],
            stage="llm_invocation",
            validation=validation_data,
            vulnerability=vulnerability,
            details=invocation.get("details"),
        )

    response = invocation["response"]
    output_valid, output_issues = OutputValidator.validate(response)
    if not output_valid:
        return _blocked(
            "LLM response failed output validation",
            stage="output_validation",
            validation=validation_data,
            vulnerability=vulnerability,
            details={"output_issues": output_issues},
        )

    return {
        "status": "success",
        "reason": "",
        "stage": "completed",
        "validation": validation_data,
        "vulnerability": vulnerability,
        "output_validation": {"is_valid": True, "issues": []},
        "response": response,
        "metadata": invocation["metadata"],
        "prompt_path": invocation["prompt_path"],
    }


def execute_process_workflow(payload: UserInputPayload) -> Dict[str, Any]:
    """Detailed multi-step flow used by POST /process."""
    validation = InputValidator.validate(payload.user_input)
    validation_data = _validation_payload(validation)

    risk = assess_injection_risk(payload.user_input)
    vulnerability = build_vulnerability_analysis(
        payload.user_input,
        analyze_safe_template=payload.analyze_safe_template,
        risk=risk,
    )

    workflow: Dict[str, Any] = {
        "validation": validation_data,
        "vulnerability": vulnerability,
        "risk_assessment": risk,
        "invocation": None,
        "output_validation": None,
        "status": "blocked",
        "blocked_at": None,
    }

    if not validation.is_valid:
        workflow["blocked_at"] = "input_validation"
        workflow["block_reason"] = validation.reason
        return workflow

    if risk["should_block"]:
        workflow["blocked_at"] = "vulnerability_analysis"
        workflow["block_reason"] = risk["block_reason"]
        return workflow

    try:
        invocation = _invoke_llm(payload.user_input, payload.prompt_version)
    except HTTPException:
        raise
    except Exception as exc:
        workflow["blocked_at"] = "llm_invocation"
        workflow["block_reason"] = str(exc)
        return workflow

    workflow["invocation"] = {
        "prompt_path": invocation.get("prompt_path"),
        "result": invocation,
    }

    if not invocation["ok"]:
        workflow["blocked_at"] = "llm_invocation"
        workflow["block_reason"] = invocation["reason"]
        return workflow

    output_valid, output_issues = OutputValidator.validate(invocation["response"])
    workflow["output_validation"] = {
        "is_valid": output_valid,
        "issues": output_issues,
    }

    if not output_valid:
        workflow["blocked_at"] = "output_validation"
        workflow["block_reason"] = "LLM response failed output validation"
        return workflow

    workflow["status"] = "success"
    workflow["blocked_at"] = None
    workflow["block_reason"] = None
    workflow["response"] = invocation["response"]
    workflow["metadata"] = invocation["metadata"]
    return workflow
