from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.models import State

class Router:
    """Router node for the LangGraph flow"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")
    
    def __call__(self, state: State) -> State:
        """
        Determine message intent and route to appropriate agent
        """
        message = state.message.body
        has_image = state.message.num_media > 0 and state.message.media_url
        
        # If there's an image, the prompt should consider it
        if has_image:
            prompt = [HumanMessage(
                content=[
                    {"type": "text", "text": 
                        f"""Analyze this meal: {message} Based on the message text and the fact that they sent an image and text,
                        is this likely to be food-related? Users often send pictures of meals
                        they want analyzed. Users often just send descriptions of food, expecting to get a calorie count. 
                        
                        Reply with ONLY "yes" if the message or image is likely food-related, or "no" if completely unrelated."""},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"{state.message.media_url[0]}"},
                    },
                ],
            )]
            
        else:
            prompt = f"""
            Analyze this message: "{message}"
            
            Is the user describing food, a meal, or asking about nutrition? Look for mentions of:
            - Food items (e.g. chicken, rice, vegetables)
            - Meals (e.g. breakfast, lunch, dinner)
            - Portions or servings
            - Nutrition terms (e.g. calories, protein)
            
            Reply with ONLY "yes" if the message contains ANY food/meal/nutrition content, or "no" if it's completely unrelated to food.
            """.strip().lower()
        print(f"Router prompt: {str(prompt)[:100]}...")
        response = self.llm.invoke(prompt).content.strip().lower()
        print(f"Router decision: {response}")
        
        # If message is about meal tracking, set response to indicate routing
        if "yes" in response:
            # Just pass through to meal tracking - no response needed here
            print("Routing to meal tracking")
            pass
        else:
            # For now, handle here with a simple response
            print("Routing to default response")
            state.response = "I'm not sure how to help with that. Can you tell me about a meal you'd like me to analyze or send a photo of your food?"
        
        return state
