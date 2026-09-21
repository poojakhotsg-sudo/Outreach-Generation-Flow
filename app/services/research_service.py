from app.services.scraper import scrape_website
from app.services.claude_service import analyze_research
from app.services.google_places_service import fetch_google_rating

GOOGLE_RATING_THRESHOLD = 4.5
LOW_REVIEW_COUNT_THRESHOLD = 10


async def research_business(website_url: str) -> dict:
    raw_scrape = await scrape_website(website_url)

    if not raw_scrape.get("title") and not raw_scrape.get("headers") and not raw_scrape.get("content_snippets"):
        raise ValueError("Insufficient Research: We couldn't find enough reliable information on this website.")

    structured = await analyze_research(raw_scrape)

    # Enrich with Google rating — fails silently if unavailable
    google_data = await fetch_google_rating(
        business_name=structured.get("business_name", ""),
        website_url=website_url,
    )

    if google_data is not None:
        rating = google_data["rating"]
        review_count = google_data["review_count"]

        # Store raw values for the frontend to consume
        structured["google_rating"] = rating
        structured["google_review_count"] = review_count

        # Inject into Potential Opportunities if below threshold
        if rating < GOOGLE_RATING_THRESHOLD:
            low_sample_note = (
                " (low sample size — rating may not yet be statistically reliable)"
                if review_count < LOW_REVIEW_COUNT_THRESHOLD
                else ""
            )
            opportunity = (
                f"Improve Google review rating (currently {rating}★ from {review_count} reviews, "
                f"below the {GOOGLE_RATING_THRESHOLD} threshold that signals strong local trust)"
                f"{low_sample_note}"
            )
            if "potential_opportunities" not in structured or structured["potential_opportunities"] is None:
                structured["potential_opportunities"] = []
            structured["potential_opportunities"].append(opportunity)

    return structured
