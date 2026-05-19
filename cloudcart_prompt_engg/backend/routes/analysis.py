from fastapi import APIRouter

from backend.schemas import UserInputPayload
from backend.services.vulnerability import assess_injection_risk, build_vulnerability_analysis

router = APIRouter()


@router.post("/analyze-vulnerability")
async def analyze_vulnerability(payload: UserInputPayload):
    risk = assess_injection_risk(payload.user_input)
    return build_vulnerability_analysis(
        payload.user_input,
        analyze_safe_template=payload.analyze_safe_template,
        risk=risk,
    )
