from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class UserInfo(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


class SupervisorState(BaseModel):
    messages: List[Message]
    user: Optional[UserInfo] = None
    step: str = "start"

