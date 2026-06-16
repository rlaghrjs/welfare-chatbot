from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    session_key: str
    status: str


class WelfareProfile(BaseModel):
    age: int | None = None
    lifeArray: str | None = None
    trgterIndvdlArray: str | None = None
    intrsThemaArray: str | None = None


class ChatRequest(BaseModel):
    message: str
    ctpvNm: str | None = None
    useProfile: bool = False
    profile: WelfareProfile | None = None
    

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