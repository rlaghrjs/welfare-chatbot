from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatPolicy(BaseModel):
    serv_id: str
    serv_nm: str | None = None
    serv_dgst: str | None = None
    serv_dtl_link: str | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: dict
    policies: list[ChatPolicy]