from typing import Dict, Optional, Any
from app.models.user_profile import UserProfile

class SimpleStorage:
    """Simple in-memory storage for development and testing"""
    
    def __init__(self):
        self.user_profiles = {}
        self.meal_entries = {}
        self.recipes = {}
        self.progress_logs = {}
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get a user profile by ID"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        return None
    
    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        self.user_profiles[profile.user_id] = profile
        return True
    
    async def save_meal_entry(self, meal_data: Dict) -> bool:
        """Save a meal entry"""
        user_id = meal_data.get('user_id')
        if user_id not in self.meal_entries:
            self.meal_entries[user_id] = []
        self.meal_entries[user_id].append(meal_data)
        return True
    
    async def save_recipe(self, recipe_data: Dict) -> bool:
        """Save a recipe"""
        user_id = recipe_data.get('user_id')
        if user_id not in self.recipes:
            self.recipes[user_id] = []
        self.recipes[user_id].append(recipe_data)
        return True
    
    async def save_progress(self, progress_data: Dict) -> bool:
        """Save progress data"""
        user_id = progress_data.get('user_id')
        if user_id not in self.progress_logs:
            self.progress_logs[user_id] = []
        self.progress_logs[user_id].append(progress_data)
        return True 