import json
import urllib.error
import urllib.request

from fastapi import APIRouter

from backend.services.prompt_manager import PromptVersionManager

router = APIRouter()
version_manager = PromptVersionManager()
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def _check_ollama() -> dict:
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read().decode())
        models = [m.get("name", "") for m in body.get("models", [])]
        mistral_ok = any("mistral" in name for name in models)
        return {
            "ok": mistral_ok,
            "models": models,
            "mistral_available": mistral_ok,
            "detail": "mistral ready" if mistral_ok else "pull model: ollama pull mistral",
        }
    except Exception as exc:
        return {"ok": False, "detail": str(exc), "mistral_available": False, "models": []}


@router.get("/health")
async def health_check():
    success, errors = version_manager.verify_files_exist()
    ollama = _check_ollama()
    version_info = version_manager.get_version_info()
    all_ok = success and ollama.get("mistral_available")
    return {
        "status": "ok" if all_ok else "degraded",
        "prompt_files_ok": success,
        "ollama": ollama,
        "current_prompt": version_info.get("current_version") or version_info.get("current_target"),
        "errors": errors,
    }
