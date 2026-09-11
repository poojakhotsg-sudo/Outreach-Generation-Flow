from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.claude_service import generate_problems

router = APIRouter()


class ProblemsRequest(BaseModel):
    research: dict


@router.post("/problems")
async def problems(request: ProblemsRequest):
    try:
        return await generate_problems(request.research)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="We couldn't generate the requested result. Please try again.",
        )
