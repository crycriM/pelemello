import os
import subprocess
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api", tags=["stt"])

# Default whisper-cli path
DEFAULT_WHISPER_PATH = "/home/cricri/whisper.cpp/main"
DEFAULT_MODELS_DIR = "/home/cricri/whisper.cpp/models"

def _find_whisper_path():
    if os.path.exists(DEFAULT_WHISPER_PATH):
        return DEFAULT_WHISPER_PATH
    return None

def _find_default_model():
    """Find first .bin model in models dir."""
    if not os.path.isdir(DEFAULT_MODELS_DIR):
        return None
    for f in os.listdir(DEFAULT_MODELS_DIR):
        if f.endswith(".bin"):
            return os.path.join(DEFAULT_MODELS_DIR, f)
    return None


class STTResponse(BaseModel):
    text: str

@router.post("/stt", response_model=STTResponse)
async def stt_transcribe(
    file: UploadFile,
    whisper_path: str = None,
    model: str = None,
):
    """Accept multipart audio file and transcribe using whisper-cli."""
    whisper_bin = whisper_path or _find_whisper_path()
    if not whisper_bin or not os.path.exists(whisper_bin):
        raise HTTPException(status_code=503, detail="whisper-cli not found")

    model_path = model or _find_default_model()
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=503, detail="No whisper model found")

    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [whisper_bin, "--model", model_path, "--language", "auto", tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"whisper-cli error: {result.stderr[:500]}",
            )
        # whisper-cli outputs text lines after processing
        text = result.stdout.strip()
        return STTResponse(text=text)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="whisper-cli timed out")
    finally:
        os.unlink(tmp_path)
