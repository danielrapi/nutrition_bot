from fastapi import FastAPI, Request, Response, HTTPException
from dotenv import load_dotenv
import os
import openai
from requests.auth import HTTPBasicAuth
from twilio.request_validator import RequestValidator
from datetime import datetime

from app.twilio import Twilio_Client
from app.models import WhatsAppMessage, State
from app.langgraph_flow import Workflow
from app.database import Database

# Initialize FastAPI
app = FastAPI()
# Initialize twilio client
twilio_client = Twilio_Client()
db = Database()

# Database check on startup
@app.on_event("startup")
async def startup_db_check():
    """Check database tables on startup"""
    try:
        tables = db.get_existing_tables()
        required_tables = ['workflow_states', 'meal_entries']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"WARNING: Missing required tables: {missing_tables}")
            print("Run 'python -m app.scripts.init_db' to initialize the database")
        else:
            print("Database tables verified successfully")
    except Exception as e:
        print(f"Database check failed: {e}")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        workflow = Workflow()
        workflow.save_display_graph()
        
        # Extract and validate the request data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Create a validated WhatsAppMessage object
        message = WhatsAppMessage.from_twilio_request(twilio_client, form_dict)
        print(f"Received message from {message.sender}: {message.body[:50]}...")
        # Get today's context for the user
        today_context = db.get_daily_context(
            user_id=message.sender,
            date=datetime.now()
        )
        
        #print(f"Today's context: {today_context}")
        
        # Initialize state with the message and context
        initial_state = State(
            message=message,
            context=today_context
        )
        
        # Save the initial state to the database
        initial_state_id = db.save_state(initial_state, 'initial')
        print(f"Saved initial state with ID: {initial_state_id}")
        
        # Run the graph with the initial state
        final_state = await workflow.run_graph(initial_state)
        
        # Save the final state to the database
        final_state_id = db.save_state(final_state, 'final')
        print(f"Saved final state with ID: {final_state_id}")
        
        print(f"Final state contents: {final_state}")
        response_text = final_state.get("response", "Sorry, I couldn't process your request.")
        
        message_response = twilio_client.send_message(
            message=response_text,
            to=message.sender
        )

        print(message_response)
        return {"status": "success", "message_id": message_response.sid, 
                "initial_state_id": initial_state_id, "final_state_id": final_state_id}
                
    except Exception as e:
        print(f"Error in webhook_handler: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "Nutrition Bot is running"} 