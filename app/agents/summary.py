from agents import Agent, Runner, function_tool
from app.models import State
from app.database import Database
from datetime import date, datetime
import json
import asyncio

#from app.database import DatabaseService

@function_tool
def get_meals(user_id: str, start_date: str, end_date: str):
    """
    Get all meals for a user within a specific timeframe.
    
    Args:
        user_id: The user's identifier
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD
    """
    db = Database()
    # Convert string dates to datetime objects
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        print(f"Getting meals from {start} to {end}")
        
        # Call the database method
        results = db.get_meals_for_user_and_timeframe(user_id, start, end)
        print(f"Found {len(results)} meals")
        
        # Format the results as a list of dictionaries
        meals = []
        for row in results:
            meals.append({
                "id": str(row[0]),  # Convert UUID to string
                "user_id": row[1],
                "meal_name": row[2], 
                "meal_description": row[3],
                "meal_calories": row[4],
                "meal_protein": row[5],
                "meal_carbs": row[6],
                "meal_fat": row[7],
                "created_at": str(row[8]) if row[8] else None
            })

        total_calories = sum(meal['meal_calories'] for meal in meals)
        total_protein = sum(meal['meal_protein'] for meal in meals)
        total_carbs = sum(meal['meal_carbs'] for meal in meals)
        total_fat = sum(meal['meal_fat'] for meal in meals)
        return {
            "meals": meals,
            "total_calories": total_calories,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fat": total_fat 
        }
    except Exception as e:
        print(f"Error in get_meals: {e}")
        import traceback
        traceback.print_exc()
        return []


class Summary_Creator:
    """Summary creator agent for meal tracking"""
    
    def __init__(self):
        # Create the agent with the tool
        self.agent = Agent(
            name="Summary Creator",
            instructions="""You are a nutrition assistant that creates summaries of users' meal tracking data.
            
            When asked for a summary, you should:
            1. Interpret the date range from the user's message
            2. Use the get_meals tool to retrieve their meal data
            3. Consider only days with tracked meals for the average calculation
            4. output the overview in the following format:
            📊 3-Day Nutrition Summary

            Day     | Carbs (g) | Protein (g) | Fat (g) | Calories
            --------|-----------|-------------|---------|---------
            Day 1   |   170     |     95      |   60    |  1810
            Day 2   |   165     |    112      |   60    |  1860
            Day 3   |   190     |    102      |   65    |  1940
            --------|-----------|-------------|---------|---------
            Total   |   525     |    309      |  185    |  5610
            Avg/day |  175.0    |   103.0     |  61.7   |  1870.0

            Add a one line witty comment that should both evaluate their eating but also be encouraging, adding emojis.
            """,
            tools=[get_meals],  # Use a non-static method
            model="gpt-4o-mini"
        )
    
    async def __call__(self, state: State) -> State:
        """
        Create a summary of the user's meal tracking data
        """
        print("Creating summary")
        message = state.message.body
        user_id = state.message.sender
        
        try:
            # Use the synchronous run method
            result = await Runner.run(
                starting_agent=self.agent,
                input=f"Create a summary of my meal tracking data. Today is {date.today()}. {message}. Sent by {user_id}."
            )

            print(str(result))
            # Set the response in the state
            state.response = result.final_output
            print(f"Summary: {result.final_output[:100] if result.final_output else 'No result'}...")
            
        except Exception as e:
            print(f"Error creating summary: {e}")
            import traceback
            traceback.print_exc()
            state.response = "Sorry, I couldn't create a summary of your meal tracking data. Please try again later."
        
        return state
