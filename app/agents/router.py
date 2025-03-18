from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.models import State, BinaryResponse

class Router:
    """Router node for the LangGraph flow"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(BinaryResponse)
    
    def __call__(self, state: State) -> State:
        """
        Determine message intent and route to appropriate agent
        """
        message = state.message.body
        
        # Now just handle the text content (which includes any transcriptions)
        prompt = [HumanMessage(
            content=[
                {"type": "text", "text": 
                    f"""Analyze this message: "{message}"
                    
                    Is the user describing food, a meal, or asking about nutrition? Look for mentions of:
                    - Food items (e.g. chicken, rice, vegetables)
                    - Meals (e.g. breakfast, lunch, dinner)
                    - Portions or servings
                    - Nutrition terms (e.g. calories, protein)
                    
                    True if the message contains ANY food/meal/nutrition content, or False if it's completely unrelated to food.
                    """.strip().lower()}
            ],
        )] 

        # Still handle images if present
        for media in state.message.media_items:
            if media["type"].startswith('image/'):
                prompt[0].content.append({
                    "type": "text",
                    "text": "Please also consider this image for the analysis."
                })
                prompt[0].content.append({
                    "type": "image_url", 
                    "image_url": {"url": media["url"]}
                })
        
        print(f"Router prompt: {str(prompt)[:150]}...")
        response = self.llm.invoke(prompt)
        print(f"Router decision: {response.bin_outcome}")
        print(f"Router reasoning: {response.reasoning}")
        
        # If message is about meal tracking, set response to indicate routing
        if response.bin_outcome:
            # Just pass through to meal tracking - no response needed here
            print("Routing to meal tracking")
            pass
        else:
            # For now, handle here with a simple response
            print("Routing to default response")
            state.response = "I'm not sure how to help with that. Can you tell me about a meal you'd like me to analyze or send a photo of your food?"
        
        return state
