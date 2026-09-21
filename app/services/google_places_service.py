import httpx
import re
import json
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APIFY_RUN_SYNC_URL = (
    "https://api.apify.com/v2/actors/compass~crawler-google-places"
    "/run-sync-get-dataset-items"
)

# Timeout for the Apify sync run — actor can be slow on cold start
APIFY_TIMEOUT_SECONDS = 45.0


def _normalize(text: str) -> str:
    """Lowercase and strip punctuation/whitespace for fuzzy matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _extract_domain(url: str) -> str:
    """Extract bare domain tokens from a URL, e.g. 'sigasystems' from 'https://sigasystems.com'."""
    match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
    if match:
        domain = match.group(1)
        # Strip TLD (.com, .io, etc.) to get just the name
        domain = re.sub(r"\.[a-z]{2,}$", "", domain)
        return _normalize(domain)
    return ""


def _is_plausible_match(matched_name: str, matched_address: str,
                        business_name: str, website_url: str) -> bool:
    """
    Sanity-check that the Apify result is the business we searched for.
    Returns False if it looks like a clear mismatch.
    """
    norm_matched = _normalize(matched_name)
    norm_searched = _normalize(business_name)
    domain_tokens = _extract_domain(website_url)

    # Accept if any significant token from the search name appears in the result name
    if norm_searched and len(norm_searched) > 3:
        if norm_searched in norm_matched or norm_matched in norm_searched:
            return True
        # Try word-by-word: accept if any name word ≥ 4 chars overlaps
        for word in re.split(r"\s+", business_name.lower()):
            w = _normalize(word)
            if len(w) >= 4 and w in norm_matched:
                return True

    # Also accept if domain tokens appear in the matched name
    if domain_tokens and len(domain_tokens) >= 4:
        if domain_tokens in norm_matched:
            return True

    return False


async def fetch_google_rating(
    business_name: str,
    website_url: str,
    location: str | None = None,
) -> dict | None:
    """
    Fetches the Google rating and review count for a business via the
    Apify compass/crawler-google-places actor (sync mode).

    Returns a dict:
        {
            "rating": 4.2,
            "review_count": 87,
            "matched_name": "...",
            "matched_address": "..."
        }
    or None if unavailable / mismatched / token absent.
    Fails gracefully — never raises, never crashes the research pipeline.
    """
    token = settings.APIFY_API_TOKEN
    if not token:
        logger.warning("No APIFY_API_TOKEN found, skipping Google Places lookup.")
        return None

    # The user explicitly requested to use website_url exactly.
    search_query = website_url

    payload = {
        "enableCompetitorAnalysis": False,
        "includeWebResults": False,
        "language": "en",
        "maxCompetitorsToAnalyze": 30,
        "maxCrawledPlacesPerSearch": 50,
        "maximumLeadsEnrichmentRecords": 0,
        "scrapeContacts": False,
        "scrapeDirectories": False,
        "scrapeImageAuthors": False,
        "scrapeOrderOnline": False,
        "scrapePlaceDetailPage": False,
        "scrapeReviewsPersonalData": True,
        "scrapeSocialMediaProfiles": {
            "facebooks": False,
            "instagrams": False,
            "tiktoks": False,
            "twitters": False,
            "youtubes": False,
        },
        "scrapeTableReservationProvider": False,
        "searchStringsArray": [search_query],
        "skipClosedPlaces": False,
        "verifyLeadsEnrichmentEmails": False,
    }

    logger.info(f"Sending request to Apify for URL: {search_query}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=APIFY_TIMEOUT_SECONDS) as client:
            response = await client.post(
                APIFY_RUN_SYNC_URL,
                params={"token": token},
                json=payload,
            )
            response.raise_for_status()
            items = response.json()

        logger.info(f"Raw response from Apify received. Number of items: {len(items) if isinstance(items, list) else 0}")
        logger.info(f"Raw Response: {json.dumps(items, indent=2)}")

        if not items or not isinstance(items, list):
            logger.warning("Result array is empty or invalid.")
            return None

        place = items[0]
        rating = place.get("rating") or place.get("totalScore")
        review_count = place.get("reviewsCount") or place.get("userRatingsTotal") or 0
        matched_name = place.get("title") or place.get("name") or ""
        matched_address = place.get("address") or ""

        if rating is None:
            logger.warning("A place was matched, but it has no rating.")
            return None

        # Sanity-check: make sure this is actually the business we searched for
        is_match = _is_plausible_match(matched_name, matched_address, business_name, website_url)
        logger.info(f"Matched Place: '{matched_name}' at '{matched_address}'. Rating: {rating}, Reviews: {review_count}. Plausible match? {is_match}")
        
        if not is_match:
            return None

        return {
            "rating": round(float(rating), 1),
            "review_count": int(review_count),
            "matched_name": matched_name,
            "matched_address": matched_address,
        }

    except Exception as e:
        logger.error(f"Error fetching Google rating from Apify: {str(e)}")
        # Silently swallow all errors — Google rating is a nice-to-have signal
        return None
