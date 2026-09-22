from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.claude_service import guide_offer, suggest_solution, suggest_final_offer

router = APIRouter()


class OfferRequest(BaseModel):
    selected_problems: List[Dict[str, Any]]
    initial_solution: str
    research: Dict[str, Any] = {}
    additional_context: str = ""


class SuggestSolutionRequest(BaseModel):
    selected_problems: List[Dict[str, Any]]
    research: Dict[str, Any] = {}
    additional_context: str = ""


@router.post("/suggest-solution")
async def get_suggested_solution(request: SuggestSolutionRequest):
    try:
        suggestion = await suggest_solution(request.selected_problems, request.research, request.additional_context)
        return {"suggestion": suggestion}
    except Exception as e:
        print(f"Error generating suggested solution: {e}")
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")


@router.post("/offer-guide")
async def get_offer_guide(request: OfferRequest):
    try:
        guidance = await guide_offer(request.selected_problems, request.initial_solution, request.research, request.additional_context)
        suggested_final_offer = await suggest_final_offer(
            request.selected_problems, request.research, request.initial_solution, guidance, request.additional_context
        )
        return {"guidance": guidance, "suggested_final_offer": suggested_final_offer}
    except Exception as e:
        import traceback
        print(f"Error generating offer guide: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")
