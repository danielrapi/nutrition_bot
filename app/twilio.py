from twilio.rest import Client
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
import requests
import json
from base64 import b64encode
import tempfile
from typing import Dict, Any
class Twilio_Client:
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        self.TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
        self.TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

        # Print debug info
        print("=== Twilio Credentials Debug ===")
        print(f"Account SID: {self.TWILIO_ACCOUNT_SID}")
        print(f"Auth Token: {self.TWILIO_AUTH_TOKEN}")
        print("=============================")

        # Initialize clients
        self.twilio_client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)
        self.twilio_validator = RequestValidator(self.TWILIO_AUTH_TOKEN)
        self.twilio_auth = HTTPBasicAuth(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)

    
    def send_message(self, message, to):
        try:
            message_response = self.twilio_client.messages.create(
                from_=self.TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=to
            )

            #print message sent
            print(f"Message sent with SID: {message_response.sid}")
            return message_response
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

    def get_media_url(self, media_type, media_url: str) -> Dict[str, Any]:
        """Download media content and process based on type"""
        
        response = requests.get(
            media_url,
            auth=self.twilio_auth
        )
        
        if media_type.startswith('image/'):
            # For images, return as data URL
            image_data = response.content
            tmp = b64encode(image_data).decode('utf-8')
            url = f"data:{media_type};base64,{tmp}"
            return {"type": media_type, "url": url}
        
        elif media_type.startswith('audio/'):
            # For audio, save to temp file AND encode as base64
            # First save the audio to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                temp_audio.write(response.content)
                temp_audio_path = temp_audio.name
            
            # Also encode the audio as base64 for direct API use
            base64_audio = b64encode(response.content).decode('utf-8')
            
            return {
                "type": media_type, 
                "file_path": temp_audio_path,  # Path to the saved file
                "base64_data": base64_audio    # Base64 encoded data
            }
        else:
            raise ValueError(f"Unsupported media type: {media_type}")