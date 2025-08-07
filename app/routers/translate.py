from fastapi import APIRouter
from app.models.query_request import QueryRequest
from app.models.query_response import QueryResponse
from app.services.llm_service import generate_query

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def translate_nl_to_query(request: QueryRequest):
    query = await generate_query(request)
    return QueryResponse(query=query)
