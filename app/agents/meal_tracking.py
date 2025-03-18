from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.models import State, MealEntry
import json
from app.database import Database
from sqlalchemy import text

#from app.database import DatabaseService

class Meal_Tracker:
    """Meal tracking agent for nutrition analysis"""
    
    def __init__(self):
        # Use different models based on whether we're analyzing text or images
        self.llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(MealEntry)
        self.db = Database()
    
    def __call__(self, state: State) -> State:
        """
        Process meal descriptions and extract structured nutrition data
        """
        if state.response:
            # If response is already set by router, just return
            return state
            
        message = state.message.body  # Already contains transcription
        user_id = state.message.sender

        prompt = [HumanMessage(
            content=[
                {"type": "text", "text": f"Analyze this meal description: {message}"},
            ],
        )]

        # Only handle images now, since audio has been transcribed
        for media in state.message.media_items:
            if media["type"].startswith("image/"):
                prompt[0].content.append({
                    "type": "image_url", 
                    "image_url": {"url": media["url"]}
                })

        # Call the model with the simplified prompt
        response = self.llm.invoke(prompt)
        state.meal_entry = response
        
        # Save to database, etc...
        try:
            user_id = state.message.sender
            self.db.set_meal_entry(user_id, state.meal_entry)
            state.db_operation_status = "success"
        except Exception as e:
            print(f"Database error: {e}")
            state.db_operation_status = f"error: {str(e)}"
        
        return state
