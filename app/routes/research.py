from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.research_service import research_business

router = APIRouter()


class ResearchRequest(BaseModel):
    website_url: str


@router.post("/research")
async def process_research(request: ResearchRequest):
    try:
        research = await research_business(request.website_url)
        return {"research": research}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"We couldn't access this website. Please check the URL and try again. ({str(e)})")
