from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from app.models.user_profile import UserProfile

class ContextManager:
    """
    Manages conversation history and user context for AI interactions.
    Provides enriched context for more personalized and contextually aware responses.
    """
    
    def __init__(self, storage_service):
        """
        Initialize the context manager with a storage service.
        
        Args:
            storage_service: Database service for retrieving and storing data
        """
        self.storage = storage_service
        self.max_conversation_history = 10  # Maximum number of messages to include in history
        
    async def get_enriched_context(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """
        Build a comprehensive context object for the AI, including:
        - User profile information
        - Recent conversation history
        - Nutritional data (daily intake, recent meals)
        - Progress data
        
        Args:
            user_id: The user's identifier
            current_message: The current message from the user
            
        Returns:
            Dict containing all context information
        """
        # Get basic user profile
        user_profile = await self.storage.get_user_profile(user_id)
        if not user_profile:
            return {"error": "User profile not found"}
            
        # Get conversation history
        conversation_history = await self.get_conversation_history(user_id)
        
        # Get nutritional context
        nutrition_context = await self.get_nutrition_context(user_id)
        
        # Get progress context
        progress_context = await self.get_progress_context(user_id)
        
        # Combine all context
        return {
            "user_profile": self._format_user_profile(user_profile),
            "conversation_history": conversation_history,
            "nutrition_context": nutrition_context,
            "progress_context": progress_context,
            "current_message": current_message,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_user_profile(self, profile: UserProfile) -> Dict[str, Any]:
        """Format user profile data for context"""
        if not profile:
            return {}
            
        return {
            "user_id": profile.user_id,
            "height": profile.height,
            "weight": profile.weight,
            "age": profile.age,
            "activity_level": profile.activity_level,
            "goal": profile.goal,
            "onboarding_complete": profile.onboarding_complete,
            "created_at": profile.created_at.isoformat() if hasattr(profile.created_at, 'isoformat') else str(profile.created_at),
            "updated_at": profile.updated_at.isoformat() if hasattr(profile.updated_at, 'isoformat') else str(profile.updated_at)
        }
    
    async def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history for the user
        
        Args:
            user_id: The user's identifier
            
        Returns:
            List of conversation messages with role and content
        """
        # This will need to be implemented in the database service
        try:
            history = await self.storage.get_conversation_history(
                user_id, 
                limit=self.max_conversation_history
            )
            return history
        except AttributeError:
            # If the method doesn't exist yet
            return []
    
    async def save_message(self, user_id: str, role: str, content: str) -> bool:
        """
        Save a message to the conversation history
        
        Args:
            user_id: The user's identifier
            role: Either 'user' or 'assistant'
            content: The message content
            
        Returns:
            Success status
        """
        try:
            return await self.storage.save_conversation_message(
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.now()
            )
        except AttributeError:
            # If the method doesn't exist yet
            return False
    
    async def get_nutrition_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get nutritional context including daily intake and recent meals
        
        Args:
            user_id: The user's identifier
            
        Returns:
            Dict with nutritional context
        """
        # Get today's nutrition summary
        try:
            daily_nutrition = await self.storage.get_daily_nutrition(user_id)
        except (AttributeError, Exception):
            daily_nutrition = {}
            
        # Get recent meals
        try:
            recent_meals = await self.storage.get_meal_history(user_id, limit=5)
        except (AttributeError, Exception):
            recent_meals = []
            
        # Get nutrition history for the past week
        try:
            nutrition_history = await self.storage.get_nutrition_history(user_id, days=7)
        except (AttributeError, Exception):
            nutrition_history = []
            
        return {
            "daily_nutrition": daily_nutrition,
            "recent_meals": recent_meals,
            "nutrition_history": nutrition_history
        }
    
    async def get_progress_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get progress tracking context
        
        Args:
            user_id: The user's identifier
            
        Returns:
            Dict with progress context
        """
        try:
            progress_history = await self.storage.get_progress_history(user_id, limit=5)
            return {"progress_history": progress_history}
        except (AttributeError, Exception):
            return {"progress_history": []}
            
    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a comprehensive system prompt using the context
        
        Args:
            context: The enriched context dictionary
            
        Returns:
            Formatted system prompt string
        """
        user_profile = context.get("user_profile", {})
        nutrition = context.get("nutrition_context", {})
        progress = context.get("progress_context", {})
        
        # Format daily nutrition data
        daily_nutrition = nutrition.get("daily_nutrition", {})
        calories_consumed = daily_nutrition.get("total_calories", 0)
        target_calories = daily_nutrition.get("target_calories", 0)
        remaining_calories = target_calories - calories_consumed if target_calories > 0 else "unknown"
        
        # Build the system prompt
        prompt = f"""You are a personalized nutrition assistant helping a user with the following profile:

USER PROFILE:
- Height: {user_profile.get('height', 'unknown')} cm
- Weight: {user_profile.get('weight', 'unknown')} kg
- Age: {user_profile.get('age', 'unknown')} years
- Activity Level: {user_profile.get('activity_level', 'unknown')}
- Goal: {user_profile.get('goal', 'unknown')}

TODAY'S NUTRITION (so far):
- Calories: {calories_consumed}/{target_calories} kcal ({remaining_calories} remaining)
- Protein: {daily_nutrition.get('total_protein', 0)}g
- Carbs: {daily_nutrition.get('total_carbs', 0)}g
- Fats: {daily_nutrition.get('total_fats', 0)}g

"""

        # Add recent meals if available
        recent_meals = nutrition.get("recent_meals", [])
        if recent_meals:
            prompt += "RECENT MEALS:\n"
            for i, meal in enumerate(recent_meals[:3], 1):
                meal_date = meal.get('meal_date', 'unknown date')
                meal_type = meal.get('meal_type', 'meal')
                calories = meal.get('calories', 0)
                prompt += f"- {meal_type} ({meal_date}): {meal.get('description', 'No description')} ({calories} kcal)\n"
            prompt += "\n"
            
        # Add progress information if available
        progress_history = progress.get("progress_history", [])
        if progress_history:
            latest_progress = progress_history[0]
            prompt += f"LATEST PROGRESS UPDATE ({latest_progress.get('log_date', 'unknown date')}):\n"
            prompt += f"- Weight: {latest_progress.get('weight', 'unknown')} kg\n"
            if latest_progress.get('notes'):
                prompt += f"- Notes: {latest_progress.get('notes')}\n"
            prompt += "\n"
            
        # Add instructions for the AI
        prompt += f"""When responding to the user:
1. Be personalized - reference their specific goals, metrics, and history
2. Be concise - keep responses under 1500 characters
3. Be helpful - provide actionable advice based on their nutritional data
4. Be conversational - maintain a friendly, encouraging tone

Remember their goal is {user_profile.get('goal', 'unknown')} and tailor your advice accordingly.
"""
        
        return prompt 