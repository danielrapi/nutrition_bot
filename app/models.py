from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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
    #create uuid by default
    #id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    #user_id: int
    meal_name: str
    meal_description: str
    #meal_date: datetime = Field(default_factory=datetime.now)
    meal_calories: int
    meal_protein: int
    meal_carbs: int
    meal_fat: int

# State Class
class State(BaseModel):
    """State class for the LangGraph flow"""
    message: WhatsAppMessage
    meal_entry: Optional[MealEntry] = None
    response: Optional[str] = None
    db_operation_status: Optional[str] = None
    
    #class Config:
   #     frozen = True  # Make the model immutable and hashable
