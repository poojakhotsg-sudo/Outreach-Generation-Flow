from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.claude_service import suggest_solution, guide_offer, suggest_final_offer

router = APIRouter()


class SuggestSolutionRequest(BaseModel):
    selected_problems: list
    research: dict = {}
    additional_context: str = ""


class OfferGuideRequest(BaseModel):
    selected_problems: list
    initial_solution: str
    research: dict = {}
    additional_context: str = ""


@router.post("/suggest-solution")
async def suggest_solution_route(request: SuggestSolutionRequest):
    try:
        suggestion = await suggest_solution(request.selected_problems, request.research, request.additional_context)
        return {"suggestion": suggestion}
    except Exception:
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")


@router.post("/offer-guide")
async def offer_guide_route(request: OfferGuideRequest):
    try:
        guidance = await guide_offer(
            request.selected_problems, request.initial_solution, request.research,
            request.additional_context,
        )
        suggested_final_offer = await suggest_final_offer(
            request.selected_problems, request.research, request.initial_solution, guidance,
            request.additional_context,
        )
        return {"guidance": guidance, "suggested_final_offer": suggested_final_offer}
    except Exception:
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")
