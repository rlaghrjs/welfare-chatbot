from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    session_key: str
    status: str


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    answer: str
    intent: dict
    request_url: str | None = None
    saved_count: int = 0
    skipped_count: int = 0
    policies: list[dict] = []


class EndSessionResponse(BaseModel):
    session_key: str
    status: str
    summary: str | None = None