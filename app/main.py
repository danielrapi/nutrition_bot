from fastapi import FastAPI, Request, Response, HTTPException
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
import os
import openai
from requests.auth import HTTPBasicAuth
from crewai import LLM

# Import services
from app.services.media_processor import MediaProcessor
from app.services.message_processor import MessageProcessor
from app.services.onboarding_service import OnboardingService
from app.agents.nutrition_agent import NutritionAgents
from app.services.simple_storage import SimpleStorage

# Load environment variables
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

# Initialize FastAPI
app = FastAPI()

# Print debug info
print("=== Twilio Credentials Debug ===")
print(f"Account SID: {TWILIO_ACCOUNT_SID}")
print(f"Auth Token: {TWILIO_AUTH_TOKEN}")
print("=============================")

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)
twilio_auth = HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize shared LLM
llm = LLM(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=4096
)

# Initialize services
storage = SimpleStorage()
media_processor = MediaProcessor(openai_client, twilio_auth)
nutrition_agents = NutritionAgents(llm)
onboarding_service = OnboardingService(llm, storage)
message_processor = MessageProcessor(nutrition_agents, media_processor, storage, onboarding_service)

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        # Validate Twilio request
        form_data = await request.form()
        url = str(request.url)
            
        incoming_msg = form_data.get('Body', '').strip()
        sender = form_data.get('From', '')
        print(sender)
        num_media = int(form_data.get('NumMedia', 0))
        media_type = form_data.get('MediaContentType0', '')
        
        print(f"Received message from {sender}: {incoming_msg[:50]}...")
        
        print(1)
        # Process the message
        response_text = await message_processor.process_message(
            message=incoming_msg,
            sender=sender,
            num_media=num_media,
            media_type=media_type,
            form_data=form_data
        )

        # Send response
        print(f"Sending response: {response_text[:100]}...")
        
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=response_text,
            to=sender
        )

        print(f"Message sent with SID: {message.sid}")
        return {"status": "success", "message_sid": message.sid}
        
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        return {"status": "error", "message": he.detail}
    except Exception as e:
        print(f"Error in webhook_handler: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "Nutrition Bot is running"} 