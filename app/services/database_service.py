from typing import Dict, Optional
import asyncpg
from app.models.user_profile import UserProfile
import json

class DatabaseService:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by ID
        
        Note: user_id is the user's phone number from Twilio (e.g. "whatsapp:+1234567890")
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM user_profiles WHERE user_id = $1", 
                    user_id
                )
                
                if row:
                    # Convert to dict and then to UserProfile
                    data = dict(row)
                    return UserProfile.from_dict(data)
                return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        try:
            profile_dict = profile.to_dict()
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_profiles 
                    (user_id, height, weight, age, activity_level, goal, onboarding_complete, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        height = $2,
                        weight = $3,
                        age = $4, 
                        activity_level = $5,
                        goal = $6,
                        onboarding_complete = $7,
                        updated_at = $9
                    """,
                    profile_dict["user_id"],
                    profile_dict["height"],
                    profile_dict["weight"],
                    profile_dict["age"],
                    profile_dict["activity_level"],
                    profile_dict["goal"],
                    profile_dict["onboarding_complete"],
                    profile_dict["created_at"],
                    profile_dict["updated_at"]
                )
                return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False

    async def save_meal_entry(self, meal_data: Dict) -> bool:
        """Save a meal entry"""
        try:
            async with self.db_pool.acquire() as conn:
                # Extract values from meal_data
                user_id = meal_data['user_id']
                meal_description = meal_data.get('meal_description', '')
                meal_type = meal_data.get('meal_type', '')
                calories = meal_data.get('calories', 0)
                protein = meal_data.get('protein', 0)
                fats = meal_data.get('fats', 0)
                carbs = meal_data.get('carbs', 0)
                image_url = meal_data.get('image_url', '')
                
                await conn.execute(
                    """
                    INSERT INTO meal_entries 
                    (user_id, meal_description, meal_type, calories, protein, fats, carbs, image_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    user_id, meal_description, meal_type, calories, protein, fats, carbs, image_url
                )
                return True
        except Exception as e:
            print(f"Error saving meal entry: {e}")
            return False

    async def save_recipe(self, recipe_data: Dict) -> bool:
        """Save a recipe"""
        try:
            async with self.db_pool.acquire() as conn:
                # Extract values from recipe_data
                user_id = recipe_data.get('user_id')
                name = recipe_data.get('name', '')
                ingredients = json.dumps(recipe_data.get('ingredients', {}))
                instructions = recipe_data.get('instructions', '')
                nutritional_info = json.dumps(recipe_data.get('nutritional_info', {}))
                preparation_time = recipe_data.get('preparation_time', 0)
                cooking_time = recipe_data.get('cooking_time', 0)
                meal_type = recipe_data.get('meal_type', '')
                tags = recipe_data.get('tags', [])
                
                await conn.execute(
                    """
                    INSERT INTO recipes 
                    (user_id, name, ingredients, instructions, nutritional_info, 
                    preparation_time, cooking_time, meal_type, tags)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    user_id, name, ingredients, instructions, nutritional_info,
                    preparation_time, cooking_time, meal_type, tags
                )
                return True
        except Exception as e:
            print(f"Error saving recipe: {e}")
            return False

    async def save_progress(self, progress_data: Dict) -> bool:
        """Save progress data"""
        try:
            async with self.db_pool.acquire() as conn:
                # Extract values from progress_data
                user_id = progress_data.get('user_id')
                weight = progress_data.get('weight')
                measurements = json.dumps(progress_data.get('measurements', {}))
                notes = progress_data.get('notes', '')
                mood = progress_data.get('mood', '')
                
                await conn.execute(
                    """
                    INSERT INTO progress_logs 
                    (user_id, weight, measurements, notes, mood)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id, weight, measurements, notes, mood
                )
                return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False 