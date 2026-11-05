from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.message_role import MessageRole


class AIRequest(BaseModel):
    prompt: str = Field(min_length=1)


class AIResponse(BaseModel):
    response: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: MessageRole
    content: str
    created_at: datetime | None = None