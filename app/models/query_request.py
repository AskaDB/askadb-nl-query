from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    question: str
    schema: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    examples: Optional[List[Dict[str, str]]] = None
