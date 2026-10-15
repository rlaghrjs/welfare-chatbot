from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from openai import OpenAI
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(
    prefix="/api/tts",
    tags=["TTS"],
)

client = OpenAI(api_key=settings.openai_api_key)


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


@router.post("/speak")
def speak(request: SpeakRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="읽을 내용이 없습니다.")

    try:
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="sage",
            input=text,
            instructions="한국어로 또박또박, 친절한 말투로 읽어주세요.",
            response_format="mp3",
        )
        return Response(content=speech.content, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {str(e)}")
