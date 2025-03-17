from fastapi import FastAPI, Request, Response, HTTPException
from dotenv import load_dotenv
import os
import openai
from requests.auth import HTTPBasicAuth
from twilio.request_validator import RequestValidator

from app.twilio import Twilio_Client
from app.models import WhatsAppMessage, State
from app.langgraph_flow import Workflow

# Initialize FastAPI
app = FastAPI()
# Initialize twilio client
twilio_client = Twilio_Client()
# Initialize workflow (only once, outside the request handler)
workflow = Workflow()

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        # Extract and validate the request data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Create a validated WhatsAppMessage object
        message = WhatsAppMessage.from_twilio_request(twilio_client, form_dict)
        
        print(f"Received message from {message.sender}: {message.body[:50]}...")
        
        # Initialize state with the message
        initial_state = State(message=message)
        #print(initial_state)
        
        # Run the graph with the initial state - using the pre-initialized workflow
        final_state = workflow.run_graph(initial_state)
        
        #print(f"Final state contents: {final_state}")
        response_text = final_state.get("response", "Sorry, I couldn't process your request.")
        
        message_response = twilio_client.send_message(
            message=response_text,
            to=message.sender
        )

        print(message_response)
        return {"status": "success", "message_id": message_response.sid}
    except Exception as e:
        print(f"Error in webhook_handler: {e}")
        print(f"Error type: {type(e)}")
        # Print the full error traceback for debugging
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "Nutrition Bot is running"} 