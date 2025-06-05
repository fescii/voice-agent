"""
ElevenLabs Text-to-Speech service implementation.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
import httpx
from io import BytesIO

from core.config.services.tts.elevenlabs import ElevenLabsConfig
from core.logging import get_logger

logger = get_logger(__name__)


class ElevenLabsService:
    """ElevenLabs TTS service for converting text to speech."""
    
    def __init__(self, config: ElevenLabsConfig):
        """Initialize ElevenLabs service."""
        self.config = config
        self.client = httpx.AsyncClient(
            base_url="https://api.elevenlabs.io/v1",
            headers={
                "xi-api-key": config.api_key,
                "Content-Type": "application/json"
            }
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to config default)
            model_id: Model ID to use (defaults to config default)
            voice_settings: Voice settings override
            
        Returns:
            Audio data as bytes
        """
        voice_id = voice_id or self.config.default_voice_id
        model_id = model_id or self.config.default_model_id
        
        if not voice_settings:
            voice_settings = {
                "stability": self.config.stability,
                "similarity_boost": self.config.similarity_boost,
                "style": self.config.style,
                "use_speaker_boost": self.config.use_speaker_boost
            }
        
        try:
            logger.info(f"Synthesizing speech with voice_id: {voice_id}")
            
            response = await self.client.post(
                f"/text-to-speech/{voice_id}",
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": voice_settings
                }
            )
            response.raise_for_status()
            
            audio_data = response.content
            logger.info(f"Successfully synthesized {len(audio_data)} bytes of audio")
            
            return audio_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            raise
    
    async def synthesize_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1024
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize speech from text as a stream.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            model_id: Model ID to use
            voice_settings: Voice settings override
            chunk_size: Size of chunks to yield
            
        Yields:
            Audio data chunks as bytes
        """
        voice_id = voice_id or self.config.default_voice_id
        model_id = model_id or self.config.default_model_id
        
        if not voice_settings:
            voice_settings = {
                "stability": self.config.stability,
                "similarity_boost": self.config.similarity_boost,
                "style": self.config.style,
                "use_speaker_boost": self.config.use_speaker_boost
            }
        
        try:
            logger.info(f"Starting streaming synthesis with voice_id: {voice_id}")
            
            async with self.client.stream(
                "POST",
                f"/text-to-speech/{voice_id}/stream",
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": voice_settings
                }
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_bytes(chunk_size):
                    yield chunk
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs streaming API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming synthesis: {str(e)}")
            raise
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices.
        
        Returns:
            Dictionary containing voice information
        """
        try:
            response = await self.client.get("/voices")
            response.raise_for_status()
            
            voices_data = response.json()
            logger.info(f"Retrieved {len(voices_data.get('voices', []))} voices")
            
            return voices_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting voices: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            raise
    
    async def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """
        Get information about a specific voice.
        
        Args:
            voice_id: ID of the voice
            
        Returns:
            Voice information
        """
        try:
            response = await self.client.get(f"/voices/{voice_id}")
            response.raise_for_status()
            
            voice_info = response.json()
            logger.info(f"Retrieved info for voice: {voice_id}")
            
            return voice_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting voice info: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting voice info: {str(e)}")
            raise
    
    async def clone_voice(
        self,
        name: str,
        description: str,
        files: list[bytes],
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Clone a voice from audio samples.
        
        Args:
            name: Name for the cloned voice
            description: Description of the voice
            files: List of audio file bytes
            labels: Optional labels for the voice
            
        Returns:
            Voice ID of the cloned voice
        """
        try:
            # Prepare multipart form data
            files_data = []
            for i, file_bytes in enumerate(files):
                files_data.append(
                    ("files", (f"sample_{i}.wav", BytesIO(file_bytes), "audio/wav"))
                )
            
            data = {
                "name": name,
                "description": description
            }
            
            if labels:
                data["labels"] = labels
            
            response = await self.client.post(
                "/voices/add",
                data=data,
                files=files_data
            )
            response.raise_for_status()
            
            result = response.json()
            voice_id = result.get("voice_id")
            
            logger.info(f"Successfully cloned voice: {voice_id}")
            return voice_id
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error cloning voice: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error cloning voice: {str(e)}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
