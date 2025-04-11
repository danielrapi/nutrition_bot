from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from app.twilio import Twilio_Client

import uuid


class WhatsAppMessage(BaseModel):
    """Model representing an incoming WhatsApp message from Twilio"""
    body: str = Field(default="")
    sender: str
    num_media: int = 0
    media_items: Optional[List[Dict[str, Any]]] = None  # Store media info
    form_data: Dict[str, Any]
    
    @classmethod
    def from_twilio_request(cls, twilio_client: Twilio_Client, form_data: Dict[str, Any]):
        """
        Create a WhatsAppMessage from Twilio form data
        
        Args:
            form_data: Dictionary containing Twilio webhook form data
            
        Returns:
            WhatsAppMessage: Validated message object
        """
        # Extract media URL if present
        media_items = []
        for i in range(int(form_data.get('NumMedia', 0))):
            media_type = form_data.get(f'MediaContentType{i}', '')
            tmp_media_url = form_data.get(f'MediaUrl{i}', None)
            media_items.append(twilio_client.get_media_url(media_type, tmp_media_url))
            
        return cls(
            body=form_data.get('Body', '').strip(),
            sender=form_data.get('From', ''),
            num_media=int(form_data.get('NumMedia', 0)),
            media_items=media_items,
            form_data=form_data
        )

class BinaryResponse(BaseModel):
    """Model representing a binary response from the agent"""
    bin_outcome: bool
    reasoning: str

class MealEntry(BaseModel):
    """Model representing a meal entry in the database"""
    id: Optional[str] = None  # Add ID field
    meal_name: str
    meal_description: str
    meal_calories: int
    meal_protein: int
    meal_carbs: int
    meal_fat: int

# Add these new models
class MealContext(BaseModel):
    """Model representing a single meal in the context"""
    id: str
    created_at: datetime
    meal_name: str
    meal_description: str
    meal_calories: int
    meal_protein: int
    meal_carbs: int
    meal_fat: int

class DailyContext(BaseModel):
    """Model representing the daily context of meals and totals"""
    total_calories: int = 0
    total_protein: int = 0
    total_carbs: int = 0
    total_fat: int = 0
    meals: List[MealContext] = []

    def calculate_totals(self):
        """Calculate totals from meals"""
        self.total_calories = sum(meal.meal_calories for meal in self.meals)
        self.total_protein = sum(meal.meal_protein for meal in self.meals)
        self.total_carbs = sum(meal.meal_carbs for meal in self.meals)
        self.total_fat = sum(meal.meal_fat for meal in self.meals)

# Modify the State class to include context
class State(BaseModel):
    """State class for the LangGraph flow"""
    message: WhatsAppMessage
    meal_entry: Optional[MealEntry] = None
    response: Optional[str] = None
    db_operation_status: Optional[str] = None
    intent: Optional[str] = None
    context: Optional[DailyContext] = None
    
    #class Config:
   #     frozen = True  # Make the model immutable and hashable
