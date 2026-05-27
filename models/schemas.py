from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    occupation: str
    education: str
    location: str
    situation: Optional[str] = None
    
class SchemeMatch(BaseModel):
    scheme_name: str
    description: str
    match_reason: str
    eligibility_score: float
    
class RecommendationResponse(BaseModel):
    user_profile: UserProfile
    recommendations: List[SchemeMatch]
    personalized_advice: str
