from typing import Any, Optional, Union
from pydantic import BaseModel


class UserInputPayload(BaseModel):
    user_input: str
    prompt_version: Optional[str] = "current"
    analyze_safe_template: Optional[bool] = False


class VersionSwitchPayload(BaseModel):
    target_version: str


class OutputValidationPayload(BaseModel):
    response: Union[str, dict[str, Any]]
