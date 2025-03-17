from langchain_openai import ChatOpenAI
from app.models import State
import json
#from app.database import DatabaseService

class Synthesizer:
    """To format and synthesize the final response"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")
    
    def __call__(self, state: State) -> State:
        """
        Process the user's message and provide a response
        """
        if state.response:
            # If response is already set by router, just return
            return state
         
        #meal entry details
        meal_name = state.meal_entry.meal_name
        meal_description = state.meal_entry.meal_description
        meal_calories = state.meal_entry.meal_calories
        meal_protein = state.meal_entry.meal_protein
        meal_carbs = state.meal_entry.meal_carbs
        meal_fat = state.meal_entry.meal_fat
        
        prompt = f"""
        
        Synthesize this meal into a well formated message. The details about the meal are: 
        "Meal Name: {meal_name}
        Meal Description: {meal_description}
        Meal Calories: {meal_calories}
        Meal Protein: {meal_protein}
        Meal Carbs: {meal_carbs}
        Meal Fat: {meal_fat}"
        
        Provide a response with this format:
        
        [Brief personalized comment with emojis]
        
        ⚡ Calories: X kcal
        🥩 Protein: Xg
        🥑 Fats: Xg
        🍚 Carbs: Xg
        
        [1-2 sentence motivational or witty comment]

        Keep your total response under 1500 characters for WhatsApp.
        Use friendly, encouraging language with emojis. If the meal is unhealthy, be a bit witty/sarcastic.
        """
        
        response = self.llm.invoke(prompt).content

        state.response = response
            
        return state
    