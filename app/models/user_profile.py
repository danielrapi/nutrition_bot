from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class UserProfile:
    user_id: str  # This will be the user's phone number from Twilio (e.g. "whatsapp:+1234567890")
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    age: Optional[int] = None
    activity_level: Optional[str] = None  # sedentary, light, moderate, very_active
    goal: Optional[str] = None  # weight_loss, muscle_gain, maintenance
    onboarding_complete: bool = False
    created_at: str = datetime.now().isoformat()
    updated_at: str = datetime.now().isoformat()
    
    def is_onboarding_complete(self) -> bool:
        """Check if all required fields are filled"""
        return all([
            self.height,
            self.weight,
            self.age,
            self.activity_level,
            self.goal
        ])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create a UserProfile from a dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserProfile to dictionary"""
        return {
            "user_id": self.user_id,
            "height": self.height,
            "weight": self.weight,
            "age": self.age,
            "activity_level": self.activity_level,
            "goal": self.goal,
            "onboarding_complete": self.onboarding_complete,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat()
        } 