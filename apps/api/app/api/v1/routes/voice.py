import base64
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.conversation import ConversationOrchestrator
from app.core.config import settings
from app.db.session import get_db
from app.services.voice import DeepgramVoiceService

router = APIRouter(prefix="/voice")


class VoiceStatusResponse(BaseModel):
    configured: bool
    voice_model: str
    stt_model: str
    available_voices: list[str] = [
        "aura-asteria-en",
        "aura-helios-en",
        "aura-luna-en",
        "aura-zeus-en",
        "aura-orion-en",
        "aura-arcas-en",
    ]


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1)
    voice: str | None = None


class TranscribeResponse(BaseModel):
    text: str
    confidence: float
    is_fallback: bool = False


class VoiceChatResponse(BaseModel):
    success: bool
    transcript: str
    message: str
    audio_base64: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


@router.get("/status", response_model=VoiceStatusResponse)
def get_voice_status() -> VoiceStatusResponse:
    """Check if Deepgram voice services are configured and list available models."""
    service = DeepgramVoiceService()
    return VoiceStatusResponse(
        configured=service.is_configured,
        voice_model=settings.deepgram_voice_model,
        stt_model=settings.deepgram_stt_model,
    )


@router.get("/tools")
def get_agent_tools() -> list[dict[str, Any]]:
    """Get the function calling tool definitions for Deepgram Voice Agent."""
    service = DeepgramVoiceService()
    return service.get_agent_tools_schema()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
) -> TranscribeResponse:
    """Transcribe an audio recording into text using Deepgram Nova-3."""
    service = DeepgramVoiceService()
    if not service.is_configured:
        return TranscribeResponse(
            text="Deepgram API key not configured on backend.",
            confidence=0.0,
            is_fallback=True,
        )

    audio_bytes = await file.read()
    content_type = file.content_type or "audio/webm"
    result = await service.transcribe_audio(audio_bytes=audio_bytes, content_type=content_type)
    return TranscribeResponse(
        text=result.get("text", ""),
        confidence=result.get("confidence", 1.0),
        is_fallback=result.get("is_fallback", False),
    )


@router.post("/speak")
async def speak_text(
    request: SpeakRequest,
) -> Response:
    """Generate spoken speech from text using Deepgram Aura TTS."""
    service = DeepgramVoiceService()
    if not service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Deepgram API key not configured on backend. Set DEEPGRAM_API_KEY in apps/api/.env",
        )

    audio_bytes = await service.synthesize_speech(
        text=request.text,
        voice_model=request.voice,
    )
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VoiceChatResponse:
    """Complete voice-in, voice-out turn:
    1. Transcribes dispatcher speech via Deepgram Nova-3.
    2. Runs conversational agent with MCP tools & OR-Tools optimizer.
    3. Synthesizes voice audio response via Deepgram Aura.
    """
    service = DeepgramVoiceService()
    audio_bytes = await file.read()
    content_type = file.content_type or "audio/webm"

    # Step 1: Transcribe speech
    transcription = await service.transcribe_audio(audio_bytes=audio_bytes, content_type=content_type)
    user_transcript = transcription.get("text", "").strip()

    if not user_transcript:
        return VoiceChatResponse(
            success=False,
            transcript="",
            message="No speech was detected. Please try speaking again.",
            audio_base64=None,
            data={},
        )

    # Step 2: Handle conversation with orchestrator
    orchestrator = ConversationOrchestrator(db)
    result = orchestrator.handle_message(
        session_id=UUID(session_id),
        user_message=user_transcript,
    )
    assistant_message = result.get("message", "")

    # Step 3: Synthesize voice response
    audio_base64 = None
    if service.is_configured and assistant_message:
        try:
            tts_audio = await service.synthesize_speech(text=assistant_message)
            if tts_audio:
                audio_base64 = base64.b64encode(tts_audio).decode("utf-8")
        except Exception:
            # If TTS fails, text response still succeeds
            pass

    return VoiceChatResponse(
        success=result.get("success", True),
        transcript=user_transcript,
        message=assistant_message,
        audio_base64=audio_base64,
        data=result.get("data", {}),
    )
