import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import OpenAI

from app.core.config import settings

router = APIRouter(
    prefix="/api/stt",
    tags=["STT"],
)

client = OpenAI(api_key=settings.openai_api_key)


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="오디오 파일만 업로드할 수 있습니다.")

    suffix = os.path.splitext(file.filename or "")[-1] or ".webm"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                language="ko",
            )

        return {
            "text": transcription.text,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 처리 실패: {str(e)}")

    finally:
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)