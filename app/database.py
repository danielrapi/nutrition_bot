# Database connection to supabase

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
from app.models import MealEntry

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

    # Meal related functions
    # Include Get, Set, Update, Delete
    def get_meal_entry(self, user_id: str, meal_id: str):
        result = self.connection.execute(text("SELECT * FROM meal_entries WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id})
        return result.fetchone()    
    
    def set_meal_entry(self, user_id: str, meal_entry: MealEntry):  
        #create uuid by default
        meal_entry_id = str(uuid.uuid4())
        #set datetime by default
        #meal_entry_created_at = datetime.now()

        self.connection.execute(text("INSERT INTO meal_entries (id, user_id, meal_name, meal_description, meal_calories, meal_protein, meal_carbs, meal_fat) VALUES (:id, :user_id, :meal_name, :meal_description, :meal_calories, :meal_protein, :meal_carbs, :meal_fat)"), {"id": meal_entry_id, "user_id": user_id, "meal_name": meal_entry.meal_name, "meal_description": meal_entry.meal_description, "meal_calories": meal_entry.meal_calories, "meal_protein": meal_entry.meal_protein, "meal_carbs": meal_entry.meal_carbs, "meal_fat": meal_entry.meal_fat})
        self.connection.commit()
        return True
    
    def update_meal_entry(self, user_id: str, meal_id: str, meal_entry: MealEntry):
        result = self.connection.execute(text("UPDATE meal_entries SET meal_name = :meal_name, meal_description = :meal_description, meal_calories = :meal_calories, meal_protein = :meal_protein, meal_carbs = :meal_carbs, meal_fat = :meal_fat WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id, "meal_name": meal_entry.meal_name, "meal_description": meal_entry.meal_description, "meal_calories": meal_entry.meal_calories, "meal_protein": meal_entry.meal_protein, "meal_carbs": meal_entry.meal_carbs, "meal_fat": meal_entry.meal_fat})
        self.connection.commit()
        return True

        
    def delete_meal_entry(self, user_id: str, meal_id: str):
        self.connection.execute(text("DELETE FROM meal_entries WHERE user_id = :user_id AND id = :meal_id"), {"user_id": user_id, "meal_id": meal_id})
        self.connection.commit() # Commits the current transaction, making all pending changes permanent in the database
        return True
    
    
if __name__ == "__main__":
    db = Database()
    connection = db.get_connection()
    print(connection)
    #test query
    result = connection.execute(text("SELECT * FROM meal_entries"))
    print(result.fetchall())
    db.close_connection(connection)