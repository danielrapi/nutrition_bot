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
        self.text_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(MealEntry)
        self.vision_llm = ChatOpenAI(model="gpt-4o").with_structured_output(MealEntry)
        self.db = Database()
    
    def __call__(self, state: State) -> State:
        """
        Process meal descriptions and extract structured nutrition data
        """
        if state.response:
            # If response is already set by router, just return
            return state
            
        message = state.message.body
        user_id = state.message.sender
        has_image = state.message.num_media > 0 and state.message.media_url
        
        # Different prompting based on whether there's an image
        if has_image:
            # Vision prompt with image
            prompt = HumanMessage(
                        content=[
                            {"type": "text", "text": f"Analyze this meal description: {message}"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"{state.message.media_url[0]}"},
                            },
                        ],
                    )

            # We need to use the vision model for image analysis
            response = self.vision_llm.invoke(prompt)
        else:
            # Text-only prompt
            prompt = f"""
            Analyze this meal description: "{message}"
            """
            response = self.text_llm.invoke(prompt)
        
        print(f"Extracted meal data: {response}")
        state.meal_entry = response
        
        # Explicit function call to save the meal entry
        try:
            user_id = state.message.sender
            self.db.set_meal_entry(user_id, state.meal_entry)
            # You could add a confirmation to the state
            state.db_operation_status = "success"
        except Exception as e:
            print(f"Database error: {e}")
            state.db_operation_status = f"error: {str(e)}"
        
        return state
