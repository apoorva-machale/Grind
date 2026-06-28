from fastapi import APIRouter, HTTPException

from backend.schemas import VersionSwitchPayload
from backend.services.prompt_manager import PromptVersionManager

router = APIRouter()
version_manager = PromptVersionManager()


@router.post("/switch-version")
async def switch_version(payload: VersionSwitchPayload):
    target = payload.target_version
    if target.startswith("v"):
        target = target[1:]

    success, message = version_manager.create_current_symlink(target)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {
        "success": success,
        "message": message,
        "current_version": target,
    }


@router.get("/versions")
async def get_versions():
    info = version_manager.get_version_info()
    return info
