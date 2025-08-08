from fastapi import APIRouter, HTTPException
from app.models.query_request import QueryRequest
from app.models.query_response import QueryResponse
from app.services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

@router.post("/", response_model=QueryResponse)
async def translate_nl_to_query(request: QueryRequest):
    """Convert natural language question to SQL query"""
    try:
        result = llm_service.generate_query(request)
        
        return QueryResponse(
            query=result["query"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            suggested_visualizations=result["suggested_visualizations"],
            suggested_follow_up_questions=result["suggested_follow_up_questions"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating query: {str(e)}")
