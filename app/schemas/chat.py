from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class WelfareProfile(BaseModel):
    age: int | None = None
    lifeArray: str | None = None
    trgterIndvdlArray: str | None = None
    intrsThemaArray: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: UUID | None = None
    ctpvNm: str | None = None
    useProfile: bool = False
    profile: WelfareProfile | None = None

    @field_validator("message")
    @classmethod
    def non_blank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("메시지를 입력해주세요.")
        return value.strip()
    

class ChatMessageResponse(BaseModel):
    answer: str
    intent: dict
    request_url: str | None = None
    saved_count: int = 0
    skipped_count: int = 0
    policies: list[dict] = Field(default_factory=list)
