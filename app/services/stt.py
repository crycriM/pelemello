import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api", tags=["stt"])

DEFAULT_WHISPER_HTTP_URL = "http://127.0.0.1:9000"


class STTResponse(BaseModel):
    text: str


@router.post("/stt", response_model=STTResponse)
async def stt_transcribe(
    file: UploadFile,
    whisper_url: str = DEFAULT_WHISPER_HTTP_URL,
    language: str = "auto",
    response_format: str = "text",
):
    """Transcribe audio via whisper.cpp HTTP server at port 9000."""
    url = f"{whisper_url.rstrip('/')}/inference"

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read audio: {e}")

    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(tmp_path, "rb") as f:
                form = {
                    "temperature": "0.0",
                    "response_format": response_format,
                }
                if language != "auto":
                    form["language"] = language
                files = {"file": (tmp_path, f, "audio/wav")}
                resp = await client.post(url, data=form, files=files)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Whisper server error {resp.status_code}: {resp.text[:500]}",
            )

        data = resp.json()
        if response_format == "text":
            text = data.get("text", "").strip()
        elif response_format == "json":
            text = data.get("text", "").strip()
        else:
            text = str(data)
        return STTResponse(text=text)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Whisper server timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Whisper server unreachable: {e}")
    finally:
        os.unlink(tmp_path)
