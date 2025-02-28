import os
import requests
from base64 import b64encode
import tempfile
from requests.auth import HTTPBasicAuth
import openai

class MediaProcessor:
    def __init__(self, openai_client, twilio_auth):
        self.client = openai_client
        self.twilio_auth = twilio_auth

    async def process_media(self, media_type: str, media_url: str, text_description: str = "") -> str:
        """Process different types of media attachments"""
        if media_type.startswith('image/'):
            return await self.process_image(media_url)
        elif media_type.startswith('audio/'):
            return await self.process_audio(media_url)
        return ""

    async def process_image(self, image_url: str) -> str:
        """Process image and return analysis"""
        image_data = await self._download_media(image_url)
        base64_image = b64encode(image_data).decode('utf-8')
        
        vision_response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert. Analyze the food image and provide detailed information about ingredients and portion sizes. Be specific about quantities."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this food image and provide detailed information about visible ingredients and approximate portion sizes."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        
        return vision_response.choices[0].message.content

    async def process_audio(self, audio_url: str) -> str:
        """Process audio and return transcription"""
        audio_data = await self._download_media(audio_url)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        try:
            with open(temp_audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        finally:
            os.unlink(temp_audio_path)

    async def _download_media(self, media_url: str) -> bytes:
        """Download media content with authentication"""
        response = requests.get(
            media_url,
            auth=self.twilio_auth
        )
        if response.status_code != 200:
            raise Exception(f"Failed to download media: {response.status_code}")
        return response.content 