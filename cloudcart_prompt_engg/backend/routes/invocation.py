from fastapi import APIRouter, HTTPException

from backend.schemas import UserInputPayload
from backend.services.prompt_manager import PromptManager
from backend.services.workflow import (
    execute_process_workflow,
    execute_submit_workflow,
    resolve_prompt_path,
)

router = APIRouter()


@router.post("/invoke")
async def invoke_prompt(payload: UserInputPayload):
    prompt_path = resolve_prompt_path(payload.prompt_version)
    manager = PromptManager(prompt_path)

    if not manager.prompt_data:
        raise HTTPException(status_code=500, detail="Failed to load prompt data")

    success, template, compile_message = manager.compile()
    if not success:
        raise HTTPException(status_code=500, detail=f"Prompt compile failed: {compile_message}")

    result = manager.invoke({"user_input": payload.user_input})
    return {
        "prompt_path": prompt_path,
        "prompt_metadata": manager.get_metadata(),
        "result": result,
    }


@router.post("/process")
async def process_request(payload: UserInputPayload):
    """
    Full workflow with per-stage results:
    input validation → vulnerability → LLM → output validation.
    """
    return execute_process_workflow(payload)


@router.post("/submit")
async def submit_request(payload: UserInputPayload):
    """
    Production single-endpoint flow:
    1. Input validation (block if invalid)
    2. Vulnerability / injection-risk assessment (block if high risk)
    3. YAML PromptManager LLM invoke
    4. Output validation (block if response unsafe or malformed)
    """
    return execute_submit_workflow(payload)
