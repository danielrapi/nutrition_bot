# Database connection to supabase

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
from app.models import MealEntry, MealContext, DailyContext
from langchain_core.tools import tool
import json

load_dotenv(override=True)

class Database:
    def __init__(self):
        self.engine = create_engine(os.getenv("DATABASE_URL"))
        self.connection = self.engine.connect()

    # Get a connection to the database
    def get_connection(self):
        return self.engine.connect()
    
    # Close the connection to the database
    def close_connection(self, connection):
        connection.close()

    # Create all necessary database tables if they don't exist
    def create_tables(self):
        """Create all necessary database tables if they don't exist"""
        try:
            # First check if tables exist
            existing_tables = self.get_existing_tables()
            print(f"Existing tables: {existing_tables}")
            
            # Create workflow_states table if it doesn't exist
            if 'workflow_states' not in existing_tables:
                print("Creating workflow_states table...")
                self.connection.execute(text("""
                    CREATE TABLE workflow_states (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        state_type TEXT NOT NULL,  -- 'initial' or 'final'
                        message_body TEXT,
                        message_sender TEXT,
                        num_media INTEGER,
                        media_items JSONB,
                        meal_entry_id TEXT,
                        response TEXT,
                        db_operation_status TEXT,
                        intent TEXT
                    )
                """))
                
                # Create indices for faster querying
                self.connection.execute(text("""
                    CREATE INDEX idx_workflow_states_user_id
                    ON workflow_states(user_id)
                """))
                
                self.connection.execute(text("""
                    CREATE INDEX idx_workflow_states_timestamp 
                    ON workflow_states(timestamp)
                """))
                
                print("workflow_states table created successfully")
            else:
                print("workflow_states table already exists")
            
            # Create meal_entries table if it doesn't exist
            if 'meal_entries' not in existing_tables:
                print("Creating meal_entries table...")
                self.connection.execute(text("""
                    CREATE TABLE meal_entries (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        meal_name TEXT NOT NULL,
                        meal_description TEXT,
                        meal_calories INTEGER,
                        meal_protein INTEGER,
                        meal_carbs INTEGER,
                        meal_fat INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indices for faster querying
                self.connection.execute(text("""
                    CREATE INDEX idx_meal_entries_user_id
                    ON meal_entries(user_id)
                """))
                
                self.connection.execute(text("""
                    CREATE INDEX idx_meal_entries_created_at
                    ON meal_entries(created_at)
                """))
                
                print("meal_entries table created successfully")
            else:
                print("meal_entries table already exists")
            
            self.connection.commit()
            print("Database initialization completed successfully")
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            import traceback
            traceback.print_exc()

    def get_existing_tables(self):
        """Get a list of existing tables in the database"""
        # This query works for PostgreSQL
        result = self.connection.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        
        return [row[0] for row in result.fetchall()]

    # State Operations
    def save_state(self, state, state_type='initial'):
        """
        Save a state object to the database
        
        Args:
            state: The State object or AddableValuesDict to save
            state_type: 'initial' or 'final'
        """
        try:
            # Generate a unique ID for this state
            state_id = str(uuid.uuid4())
            
            # Handle different state object types
            if hasattr(state, 'message'):
                # Regular State object
                message = state.message
                meal_entry_id = None
                
                # If we have a meal entry, save its ID
                if hasattr(state, 'meal_entry') and state.meal_entry and hasattr(state, 'db_operation_status') and state.db_operation_status == 'success':
                    meal_entry_id = state.meal_entry.id if hasattr(state.meal_entry, 'id') else None
                    
                response = state.response if hasattr(state, 'response') else None
                db_operation_status = state.db_operation_status if hasattr(state, 'db_operation_status') else None
                intent = state.intent if hasattr(state, 'intent') else None
                
            else:
                # AddableValuesDict from LangGraph
                # Access values using dictionary-like syntax
                message = state.get('message')
                meal_entry_id = None
                
                # If we have a meal entry, save its ID
                if 'meal_entry' in state and state.get('meal_entry') and 'db_operation_status' in state and state.get('db_operation_status') == 'success':
                    meal_entry_id = state.get('meal_entry').id if hasattr(state.get('meal_entry'), 'id') else None
                    
                response = state.get('response')
                db_operation_status = state.get('db_operation_status')
                intent = state.get('intent')
            
            if not message:
                print("Warning: No message found in state")
                return None
            
            # JSON serialize the media items
            media_items_json = json.dumps([dict(item) for item in message.media_items]) if message.media_items else None
            
            # Store the state in the database
            self.connection.execute(
                text("""
                    INSERT INTO workflow_states (
                        id, user_id, state_type, message_body, message_sender,
                        num_media, media_items, meal_entry_id, response,
                        db_operation_status, intent, timestamp
                    )
                    VALUES (
                        :id, :user_id, :state_type, :message_body, :message_sender,
                        :num_media, :media_items, :meal_entry_id, :response,
                        :db_operation_status, :intent, NOW()
                    )
                """),
                {
                    "id": state_id,
                    "user_id": message.sender,
                    "state_type": state_type,
                    "message_body": message.body,
                    "message_sender": message.sender,
                    "num_media": message.num_media,
                    "media_items": media_items_json,
                    "meal_entry_id": meal_entry_id,
                    "response": response,
                    "db_operation_status": db_operation_status,
                    "intent": intent
                }
            )
            self.connection.commit()
            return state_id
        except Exception as e:
            print(f"Error saving state: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_state(self, state_id):
        """Retrieve a specific state by ID"""
        result = self.connection.execute(
            text("SELECT * FROM workflow_states WHERE id = :state_id"),
            {"state_id": state_id}
        )
        return result.fetchone()

    def get_user_states(self, user_id, limit=10):
        """Get recent states for a specific user"""
        result = self.connection.execute(
            text("""
                SELECT * FROM workflow_states 
                WHERE user_id = :user_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "limit": limit}
        )
        return result.fetchall()

    # Meal related functions
    # Include Get, Set, Update, Delete
    def get_meal_entry(self, user_id: str, meal_id: str):
        result = self.connection.execute(text("SELECT * FROM meal_entries WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id})
        return result.fetchone()    
    
    def set_meal_entry(self, user_id: str, meal_entry: MealEntry):  
        # Create uuid by default
        meal_entry_id = str(uuid.uuid4())
        
        self.connection.execute(text("""
            INSERT INTO meal_entries (
                id, user_id, meal_name, meal_description, 
                meal_calories, meal_protein, meal_carbs, meal_fat
            ) 
            VALUES (
                :id, :user_id, :meal_name, :meal_description, 
                :meal_calories, :meal_protein, :meal_carbs, :meal_fat
            )
        """), {
            "id": meal_entry_id, 
            "user_id": user_id, 
            "meal_name": meal_entry.meal_name, 
            "meal_description": meal_entry.meal_description, 
            "meal_calories": meal_entry.meal_calories, 
            "meal_protein": meal_entry.meal_protein, 
            "meal_carbs": meal_entry.meal_carbs, 
            "meal_fat": meal_entry.meal_fat
        })
        
        self.connection.commit()
        
        # Set the ID on the meal entry so it's available later
        meal_entry.id = meal_entry_id
        
        return True
    
    def update_meal_entry(self, user_id: str, meal_id: str, meal_entry: MealEntry):
        result = self.connection.execute(text("UPDATE meal_entries SET meal_name = :meal_name, meal_description = :meal_description, meal_calories = :meal_calories, meal_protein = :meal_protein, meal_carbs = :meal_carbs, meal_fat = :meal_fat WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id, "meal_name": meal_entry.meal_name, "meal_description": meal_entry.meal_description, "meal_calories": meal_entry.meal_calories, "meal_protein": meal_entry.meal_protein, "meal_carbs": meal_entry.meal_carbs, "meal_fat": meal_entry.meal_fat})
        self.connection.commit()
        return True

        
    def delete_meal_entry(self, user_id: str, meal_id: str):
        self.connection.execute(text("DELETE FROM meal_entries WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id})
        self.connection.commit() # Commits the current transaction, making all pending changes permanent in the database
        return True
    
    #Retrieve Meals for specific user and timeframe
    def get_meals_for_user_and_timeframe(self, user_id: str, start_date: datetime, end_date: datetime):
        """Retrieve meals for a specific user and timeframe"""
        print("Getting meals for user: ", user_id, " between dates: ", start_date, " and ", end_date)
        result = self.connection.execute(
            text("""
                SELECT * FROM meal_entries 
                WHERE user_id = :user_id 
                AND DATE(created_at) BETWEEN DATE(:start_date) AND DATE(:end_date)
            """), 
            {"user_id": "whatsapp:" + user_id, "start_date": start_date, "end_date": end_date}
        )
        results = result.fetchall()
        print("Result: ", results)
        
        return results

    def get_daily_context(self, user_id: str, date: datetime) -> DailyContext:
        """Get all meals for a user on a specific date and create a context object"""
        
        # Query meals for the day
        result = self.connection.execute(
            text("""
                SELECT id, created_at, meal_name, meal_description, 
                       meal_calories, meal_protein, meal_carbs, meal_fat
                FROM meal_entries 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"user_id": user_id}
        )
        
        # Convert SQLAlchemy Row objects to dictionaries
        rows = result.fetchall()
        meals = [
            MealContext(
                id=str(row[0]),  # Convert UUID to string
                created_at=row[1],
                meal_name=row[2],
                meal_description=row[3],
                meal_calories=row[4],
                meal_protein=row[5],
                meal_carbs=row[6],
                meal_fat=row[7]
            )
            for row in rows
        ]
        
        # Create and return the context
        context = DailyContext(meals=meals)
        context.calculate_totals()
        return context

if __name__ == "__main__":
    db = Database()
    connection = db.get_connection()
    print(connection)
    #test query
    result = connection.execute(text("SELECT * FROM meal_entries"))
    print(result.fetchall())
    db.close_connection(connection)