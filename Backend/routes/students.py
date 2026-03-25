from fastapi import APIRouter
from ..rag.input_pipeline import rag_query


router = APIRouter(prefix="/student", tags = ["Students API"])




@router.get("/invoke/{query}")
async def invoke_rag(query: str):
    return {"done": await rag_query(query)}