from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.claude_service import generate_outreach_email

router = APIRouter()


class GenerateEmailRequest(BaseModel):
    business_research: dict
    selected_problems: list
    final_solution_offer: str
    additional_instructions: str = ""
    additional_context: str = ""


@router.post("/generate-email")
async def generate_email_route(request: GenerateEmailRequest):
    try:
        return await generate_outreach_email(
            request.business_research,
            request.selected_problems,
            request.final_solution_offer,
            request.additional_instructions,
            request.additional_context,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")
