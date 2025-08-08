from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryResponse(BaseModel):
    query: str
    confidence: float
    explanation: Optional[str] = None
    suggested_visualizations: Optional[List[str]] = None
    suggested_follow_up_questions: Optional[List[str]] = None
