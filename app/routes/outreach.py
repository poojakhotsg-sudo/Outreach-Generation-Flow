from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.claude_service import generate_outreach_email

router = APIRouter()


class OutreachRequest(BaseModel):
    business_research: Dict[str, Any]
    selected_problems: List[Dict[str, Any]]
    final_solution_offer: str
    additional_instructions: Optional[str] = ""
    additional_context: str = ""


@router.post("/generate-email")
async def create_outreach(request: OutreachRequest):
    try:
        email_data = await generate_outreach_email(
            request.business_research,
            request.selected_problems,
            request.final_solution_offer,
            request.additional_instructions,
            request.additional_context
        )
        return email_data
    except Exception as e:
        print(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail="We couldn't generate the requested result. Please try again.")
