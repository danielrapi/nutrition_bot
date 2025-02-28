from typing import Dict, Optional
from crewai import Task, Crew
from app.services.media_processor import MediaProcessor
from app.services.simple_storage import SimpleStorage
from app.services.onboarding_service import OnboardingService
from app.agents.nutrition_agent import NutritionAgents

class MessageProcessor:
    def __init__(self, nutrition_agents: NutritionAgents, media_processor: MediaProcessor, 
                 storage: SimpleStorage, onboarding_service: OnboardingService):
        self.nutrition_agents = nutrition_agents
        self.media_processor = media_processor
        self.storage = storage
        self.onboarding_service = onboarding_service

    async def process_message(self, message: str, sender: str, num_media: int, media_type: str, form_data: dict) -> str:
        """Process incoming messages - main entry point"""
        try:
            print(2)
            # Check if user needs onboarding first
            # Note: sender (phone number) is used as the user_id
            user_profile = await self.storage.get_user_profile(sender)
            print(user_profile)
            # No profile or incomplete onboarding - handle through onboarding service
            if not user_profile or not user_profile.is_onboarding_complete():
                print(4)
                response, updates = await self.onboarding_service.process_message(sender, message)
                
                # If we got updates, save them
                if updates and user_profile:
                    for field, value in updates.items():
                        setattr(user_profile, field, value)
                    await self.storage.save_user_profile(user_profile)
                
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
            
            # Simple response for now - we'll expand this later
            return await self._handle_general_question(processed_message, sender, user_profile)
            
        except Exception as e:
            print(f"Error in process_message: {e}")
            return "I'm sorry, but I encountered an error processing your message. Please try again."

    async def _handle_general_question(self, message: str, sender: str, user_profile) -> str:
        """Handle general nutrition questions"""
        task = Task(
            description=f"Answer this nutrition-related question considering the user's goal is {user_profile.goal}: {message}",
            expected_output="Informative and helpful response",
            agent=self.nutrition_agents.agents['meal_analysis']
        )
        
        crew = Crew(
            agents=[self.nutrition_agents.agents['meal_analysis']],
            tasks=[task]
        )
        
        return str(crew.kickoff()).strip() 