from fastapi import APIRouter

from backend.schemas import OutputValidationPayload, UserInputPayload
from backend.services.input_validation import InputValidator, OutputValidator

router = APIRouter()


@router.post("/validate")
async def validate_input(payload: UserInputPayload):
    result = InputValidator.validate(payload.user_input)
    return {
        "is_valid": result.is_valid,
        "reason": result.reason,
        "violation_type": result.violation_type,
        "severity": result.severity,
    }


@router.post("/validate-output")
async def validate_output(payload: OutputValidationPayload):
    is_valid, issues = OutputValidator.validate(payload.response)
    return {
        "is_valid": is_valid,
        "issues": issues,
    }
