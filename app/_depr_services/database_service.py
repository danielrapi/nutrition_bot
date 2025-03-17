from typing import Dict, Optional, List, Any
import asyncpg
from app.models.user_profile import UserProfile
import json
import os

class DatabaseService:
    def __init__(self):
        self.pool = None
        self.db_url = os.getenv('DATABASE_URL')
        
    async def initialize(self):
        """Initialize the database connection pool"""
        if not self.pool:
            try:
                # Set statement_cache_size=0 to fix pgbouncer issue
                self.pool = await asyncpg.create_pool(
                    dsn=self.db_url,  # Data Source Name, the database connection string
                    statement_cache_size=0,  # Disable statement caching for pgbouncer compatibility
                    min_size=2,  # Minimum number of connections to maintain in the pool
                    max_size=10  # Maximum number of connections allowed in the pool
                )
                print("Database connection pool established")
                
                # Create tables if they don't exist
                await self._create_tables()
            except Exception as e:
                print(f"Error connecting to database: {e}")
                raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Create user_profiles table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    height FLOAT,
                    weight FLOAT,
                    age INTEGER,
                    activity_level TEXT,
                    goal TEXT,
                    onboarding_complete BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enhanced meal_entries table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS meal_entries (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT REFERENCES user_profiles(user_id),
                    meal_date DATE DEFAULT CURRENT_DATE,
                    meal_time TIME DEFAULT CURRENT_TIME,
                    meal_type TEXT,
                    description TEXT,
                    calories FLOAT,
                    protein FLOAT,
                    fats FLOAT,
                    carbs FLOAT,
                    fiber FLOAT,
                    sugar FLOAT,
                    sodium FLOAT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Daily nutrition logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_nutrition_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT REFERENCES user_profiles(user_id),
                    log_date DATE DEFAULT CURRENT_DATE,
                    total_calories FLOAT DEFAULT 0,
                    total_protein FLOAT DEFAULT 0,
                    total_fats FLOAT DEFAULT 0,
                    total_carbs FLOAT DEFAULT 0,
                    target_calories FLOAT,
                    water_intake FLOAT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, log_date)
                )
            ''')
            
            # Progress logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS progress_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT REFERENCES user_profiles(user_id),
                    log_date DATE DEFAULT CURRENT_DATE,
                    weight FLOAT,
                    measurements JSONB DEFAULT '{}',
                    notes TEXT,
                    mood TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Food items library table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS food_items (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT REFERENCES user_profiles(user_id),
                    name TEXT NOT NULL,
                    serving_size TEXT,
                    calories FLOAT,
                    protein FLOAT,
                    fats FLOAT,
                    carbs FLOAT,
                    fiber FLOAT,
                    sugar FLOAT,
                    sodium FLOAT,
                    is_favorite BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by ID
        
        Note: user_id is the user's phone number from Twilio (e.g. "whatsapp:+1234567890")
        """
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1", 
                user_id
            )
            
            if row:
                # Convert to dict and then to UserProfile
                data = dict(row)
                return UserProfile.from_dict(data)
            return None

    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
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
                profile.user_id,
                profile.height,
                profile.weight,
                profile.age,
                profile.activity_level,
                profile.goal,
                profile.onboarding_complete,
                profile.created_at,
                profile.updated_at
            )
            return True

    async def save_meal_entry(self, meal_data: Dict) -> bool:
        """Save a meal entry"""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            # Extract values from meal_data
            user_id = meal_data['user_id']
            
            # Fix date format issues
            meal_date = None
            if 'meal_date' in meal_data:
                # If it's a string, convert to date
                if isinstance(meal_data['meal_date'], str):
                    from datetime import datetime
                    try:
                        # Parse ISO format string to date
                        date_obj = datetime.fromisoformat(meal_data['meal_date'].replace('Z', '+00:00'))
                        meal_date = date_obj.date()  # Extract just the date part
                    except ValueError:
                        # If parsing fails, default to None (which will use CURRENT_DATE)
                        meal_date = None
                else:
                    # Already a date/datetime object
                    meal_date = meal_data['meal_date']
            
            # Fix time format issues similarly
            meal_time = None
            if 'meal_time' in meal_data:
                if isinstance(meal_data['meal_time'], str):
                    from datetime import datetime
                    try:
                        time_obj = datetime.fromisoformat(meal_data['meal_time'].replace('Z', '+00:00'))
                        meal_time = time_obj.time()  # Extract just the time part
                    except ValueError:
                        meal_time = None
                else:
                    meal_time = meal_data['meal_time']
                
            meal_type = meal_data.get('meal_type', '')
            description = meal_data.get('description', '')
            calories = meal_data.get('calories', 0)
            protein = meal_data.get('protein', 0)
            fats = meal_data.get('fats', 0)
            carbs = meal_data.get('carbs', 0)
            fiber = meal_data.get('fiber', 0)
            sugar = meal_data.get('sugar', 0)
            sodium = meal_data.get('sodium', 0)
            image_url = meal_data.get('image_url', '')
            
            # Insert meal entry
            await conn.execute(
                """
                INSERT INTO meal_entries 
                (user_id, meal_date, meal_time, meal_type, description, calories, protein, fats, carbs, 
                fiber, sugar, sodium, image_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                user_id, meal_date, meal_time, meal_type, description, calories, protein, fats, carbs,
                fiber, sugar, sodium, image_url
            )
            
            # Update daily nutrition log - using NULL for parameter placeholder if date is None
            # This will make SQL use CURRENT_DATE
            log_date = meal_date  # Use the parsed date
            
            # Try to update existing log first
            updated = await conn.execute(
                """
                UPDATE daily_nutrition_logs
                SET 
                    total_calories = total_calories + $3,
                    total_protein = total_protein + $4,
                    total_fats = total_fats + $5,
                    total_carbs = total_carbs + $6,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1 AND log_date = COALESCE($2, CURRENT_DATE)
                """,
                user_id, log_date, calories, protein, fats, carbs
            )
            
            # If no rows updated, insert new log
            if updated == "UPDATE 0":
                # Calculate target calories based on user profile
                user_profile = await self.get_user_profile(user_id)
                target_calories = 2000  # Default
                if user_profile:
                    # Simple calculation based on weight - could be more sophisticated
                    target_multiplier = 22  # Calories per kg for maintenance
                    if user_profile.goal == 'weight_loss':
                        target_multiplier = 20
                    elif user_profile.goal == 'muscle_gain':
                        target_multiplier = 24
                    
                    if user_profile.weight:
                        target_calories = user_profile.weight * target_multiplier
                
                await conn.execute(
                    """
                    INSERT INTO daily_nutrition_logs
                    (user_id, log_date, total_calories, total_protein, total_fats, total_carbs, target_calories)
                    VALUES ($1, COALESCE($2, CURRENT_DATE), $3, $4, $5, $6, $7)
                    """,
                    user_id, log_date, calories, protein, fats, carbs, target_calories
                )
            
            return True

    async def save_recipe(self, recipe_data: Dict) -> bool:
        """Save a recipe"""
        try:
            async with self.pool.acquire() as conn:
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
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
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

    async def get_meal_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get meal history for a user"""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM meal_entries 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', user_id, limit)
            
            return [dict(row) for row in rows]

    async def get_progress_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get progress history for a user"""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM progress_logs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', user_id, limit)
            
            return [dict(row) for row in rows]

    async def get_daily_nutrition(self, user_id: str, date=None) -> Dict:
        """Get daily nutrition summary for a specific date"""
        if not self.pool:
            await self.initialize()
        
        # Convert string date to proper date object if needed
        if date and isinstance(date, str):
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                date = date_obj.date()  # Extract just the date part
            except ValueError:
                date = None
        
        async with self.pool.acquire() as conn:
            log = await conn.fetchrow(
                """
                SELECT * FROM daily_nutrition_logs
                WHERE user_id = $1 AND log_date = COALESCE($2, CURRENT_DATE)
                """,
                user_id, date
            )
            
            if not log:
                # No log for this date, return empty data
                return {
                    "user_id": user_id,
                    "date": str(date) if date else "today",
                    "total_calories": 0,
                    "total_protein": 0,
                    "total_fats": 0,
                    "total_carbs": 0,
                    "target_calories": 0,
                    "water_intake": 0
                }
            
            return dict(log)
        
    async def get_nutrition_history(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get nutrition history for the past X days"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            logs = await conn.fetch(
                """
                SELECT * FROM daily_nutrition_logs
                WHERE user_id = $1 AND log_date >= CURRENT_DATE - $2::INTERVAL
                ORDER BY log_date DESC
                """,
                user_id, f"{days} days"
            )
            
            return [dict(log) for log in logs]

    async def _execute_with_retry(self, query_func, *args, **kwargs):
        """Execute a database query with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with self.pool.acquire() as conn:
                    return await query_func(conn, *args, **kwargs)
            except asyncpg.exceptions.InterfaceError as e:
                # Connection might be stale, retry
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                print(f"Database connection error, retrying ({retry_count}/{max_retries}): {e}")
                # Recreate the pool if needed
                if "connection is closed" in str(e):
                    self.pool = None
                    await self.initialize() 