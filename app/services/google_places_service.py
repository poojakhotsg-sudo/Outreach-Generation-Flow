import httpx
from app.config import settings

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


async def fetch_google_rating(business_name: str, website_url: str) -> dict | None:
    """
    Looks up the Google rating and review count for a business via the Places API.
    Returns a dict with 'rating' and 'user_ratings_total', or None if unavailable.
    Fails gracefully — never raises, never crashes the research flow.
    """
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        return None

    query = business_name if business_name and business_name.lower() != "unknown" else website_url

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: Find the Place ID
            find_resp = await client.get(FIND_PLACE_URL, params={
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,name",
                "key": api_key,
            })
            find_resp.raise_for_status()
            find_data = find_resp.json()

            candidates = find_data.get("candidates", [])
            if not candidates:
                return None

            place_id = candidates[0].get("place_id")
            if not place_id:
                return None

            # Step 2: Fetch Place Details (rating + review count)
            details_resp = await client.get(PLACE_DETAILS_URL, params={
                "place_id": place_id,
                "fields": "rating,user_ratings_total",
                "key": api_key,
            })
            details_resp.raise_for_status()
            details_data = details_resp.json()

            result = details_data.get("result", {})
            rating = result.get("rating")
            review_count = result.get("user_ratings_total")

            if rating is None:
                return None

            return {
                "rating": round(float(rating), 1),
                "user_ratings_total": int(review_count) if review_count is not None else 0,
            }

    except Exception:
        # Silently swallow all errors — Google data is a nice-to-have signal
        return None
