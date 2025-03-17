from typing import Dict, Optional
from crewai import Task, Crew
from app.services.media_processor import MediaProcessor
from app.services.simple_storage import SimpleStorage
from app.services.onboarding_service import OnboardingService
from app.agents.nutrition_agent import NutritionAgents
from app.services.context_manager import ContextManager
import json
class MessageProcessor:
    def __init__(self, nutrition_agents: NutritionAgents, media_processor: MediaProcessor, 
                 storage, onboarding_service: OnboardingService):
        self.nutrition_agents = nutrition_agents
        self.media_processor = media_processor
        self.storage = storage  # This could be either SimpleStorage or DatabaseService
        self.onboarding_service = onboarding_service
        self.context_manager = ContextManager(storage)

    async def process_message(self, message: str, sender: str, num_media: int, media_type: str, form_data: dict) -> str:
        """Process incoming messages - main entry point"""
        try:
            # Check if user needs onboarding first
            # Note: sender (phone number) is used as the user_id
            user_profile = await self.storage.get_user_profile(sender)
            print(user_profile)
            # No profile or incomplete onboarding - handle through onboarding service
            if not user_profile or not user_profile.is_onboarding_complete():
                response, updates = await self.onboarding_service.process_message(sender, message)
                
                # If we got updates, save them
                if updates and user_profile:
                    for field, value in updates.items():
                        setattr(user_profile, field, value)
                    await self.storage.save_user_profile(user_profile)
                
                # Save the conversation
                await self.context_manager.save_message(sender, 'user', message)
                await self.context_manager.save_message(sender, 'assistant', response)
                
                return response
            
            # Onboarding is complete, process media if any
            processed_message = message
            if num_media > 0:
                media_content = await self.media_processor.process_media(
                    media_type, 
                    form_data.get('MediaUrl0'),
                    message
                )
                processed_message = f"{message}\n{media_content}" if message else media_content
            
            # Save the user message to conversation history
            await self.context_manager.save_message(sender, 'user', processed_message)
            
            # Get response using context-enhanced prompting
            response = await self._handle_general_question(processed_message, sender, user_profile)
            
            try:
                response_dict = json.loads(response)  # Convert JSON response to dict
                assistant_response = response_dict.get('response', "I couldn't process your request properly.")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
                # Fallback to using the raw response if it's not valid JSON
                assistant_response = response
            
            # Save the assistant response to conversation history
            await self.context_manager.save_message(sender, 'assistant', assistant_response)
            
            return assistant_response
            
        except Exception as e:
            print(f"Error in process_message: {e}")
            return "I'm sorry, but I encountered an error processing your message. Please try again."

    async def _handle_general_question(self, message: str, sender: str, user_profile) -> str:
        """Handle general nutrition questions with enhanced context"""
        # Get enriched context
        context = await self.context_manager.get_enriched_context(sender, message)
        
        # Build system prompt with context
        system_prompt = self.context_manager.build_system_prompt(context)
        
        # Create task with enhanced context
        task = Task(
            description=f"{system_prompt}\n\nUser message: {message}",
            expected_output='JSON file with the structure: {"response": "Full formatted response with nutrient overview and all information for the user", "meals": [{"name": "Meal name", "calories": 0, "protein": 0, "carbs": 0, "fats": 0}]}',
            agent=self.nutrition_agents.agents['meal_analysis']
        )
        
        crew = Crew(
            agents=[self.nutrition_agents.agents['meal_analysis'], self.nutrition_agents.agents['recipe'], self.nutrition_agents.agents['progress']],
            tasks=[task]
        )
        
        return str(crew.kickoff()).strip() 