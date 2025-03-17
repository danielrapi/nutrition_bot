from twilio.rest import Client
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
import requests
import json
from base64 import b64encode

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

    def get_media_url(self, media_type, media_url: str) -> bytes:
        """Download media content with authentication"""
        response = requests.get(
            media_url,
            auth=self.twilio_auth
        )
        image_data = response.content
        tmp = b64encode(image_data).decode('utf-8')
        url = f"data:{media_type};base64,{tmp}"
        return url