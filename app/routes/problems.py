from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.claude_service import generate_problems

router = APIRouter()


class ProblemsRequest(BaseModel):
    research: Dict[str, Any]


@router.post("/problems")
async def identify_problems(request: ProblemsRequest):
    try:
        result = await generate_problems(request.research)
        return result
    except Exception as e:
        print(f"Error generating problems: {e}")
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")
