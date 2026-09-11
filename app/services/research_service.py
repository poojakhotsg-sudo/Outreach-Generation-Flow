from app.services.scraper import scrape_website
from app.services.claude_service import analyze_research


async def research_business(website_url: str) -> dict:
    raw_scrape = await scrape_website(website_url)

    if not raw_scrape.get("title") or not raw_scrape.get("headers") or not raw_scrape.get("content_snippets"):
        raise ValueError(
            "Insufficient Research: We couldn't find enough reliable information on this website."
        )

    return await analyze_research(raw_scrape)
