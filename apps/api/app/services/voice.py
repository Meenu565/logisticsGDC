import logging
from typing import Any
import httpx

from app.core.config import settings

logger = logging.getLogger("smart_dispatcher.voice")

DEEPGRAM_API_URL = "https://api.deepgram.com/v1"


class DeepgramVoiceService:
    """Service for handling Deepgram Speech-to-Text and Text-to-Speech interactions."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.deepgram_api_key
        self.voice_model = settings.deepgram_voice_model
        self.stt_model = settings.deepgram_stt_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your-deepgram-api-key")

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/webm",
        language: str = "en",
    ) -> dict[str, Any]:
        """Transcribe speech to text using Deepgram Nova-3.
        
        Args:
            audio_bytes: Raw audio binary data.
            content_type: MIME type of audio (e.g., 'audio/webm', 'audio/wav', 'audio/mp3').
            language: Expected language code (default 'en').
        """
        if not self.is_configured:
            logger.warning("Deepgram API key is not configured. Returning mock/test response.")
            return {
                "text": "Please configure DEEPGRAM_API_KEY in apps/api/.env",
                "confidence": 0.0,
                "is_fallback": True,
            }

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": content_type,
        }
        params = {
            "model": self.stt_model,
            "smart_format": "true",
            "punctuate": "true",
            "language": language,
            "paragraphs": "false",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{DEEPGRAM_API_URL}/listen",
                    headers=headers,
                    params=params,
                    content=audio_bytes,
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract transcript from Deepgram response structure
                channels = data.get("results", {}).get("channels", [])
                if channels and channels[0].get("alternatives"):
                    alt = channels[0]["alternatives"][0]
                    transcript = alt.get("transcript", "").strip()
                    confidence = alt.get("confidence", 1.0)
                    return {
                        "text": transcript,
                        "confidence": confidence,
                        "words": alt.get("words", []),
                        "is_fallback": False,
                    }
                return {"text": "", "confidence": 0.0, "is_fallback": False}
            except Exception as exc:
                logger.error(f"Error during Deepgram transcription: {exc}")
                raise

    async def synthesize_speech(
        self,
        text: str,
        voice_model: str | None = None,
    ) -> bytes:
        """Convert text into spoken audio using Deepgram Aura Text-to-Speech.
        
        Args:
            text: Text to synthesize.
            voice_model: Aura voice model name (default from settings: 'aura-asteria-en').
        """
        if not self.is_configured:
            logger.warning("Deepgram API key not configured for TTS.")
            return b""

        model = voice_model or self.voice_model
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }
        params = {
            "model": model,
            "encoding": "mp3",
        }
        payload = {"text": text}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{DEEPGRAM_API_URL}/speak",
                    headers=headers,
                    params=params,
                    json=payload,
                )
                response.raise_for_status()
                return response.content
            except Exception as exc:
                logger.error(f"Error during Deepgram speech synthesis: {exc}")
                raise

    def get_agent_tools_schema(self) -> list[dict[str, Any]]:
        """Return schema of dispatcher backend tools callable by a Deepgram Voice Agent."""
        return [
            {
                "name": "get_fleet_status",
                "description": "Get current status, locations, shifts, and capacities of active drivers and vehicles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status_filter": {
                            "type": "string",
                            "enum": ["all", "available", "on_route", "delayed"],
                            "description": "Optional filter for driver status.",
                        }
                    },
                },
            },
            {
                "name": "get_unassigned_orders",
                "description": "Retrieve all pending or unassigned delivery orders requiring dispatch planning.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "all"],
                            "description": "Optional order priority filter.",
                        }
                    },
                },
            },
            {
                "name": "optimize_dispatch_plan",
                "description": "Trigger OR-Tools optimization engine to generate an optimal dispatch route plan for unassigned orders.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "enum": ["balanced", "fastest", "shortest"],
                            "description": "Routing optimization objective.",
                        }
                    },
                },
            },
            {
                "name": "apply_current_plan",
                "description": "Confirm and apply the proposed dispatch plan to assign orders to vehicles and notify drivers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirmation boolean to commit the plan.",
                        }
                    },
                    "required": ["confirm"],
                },
            },
        ]
