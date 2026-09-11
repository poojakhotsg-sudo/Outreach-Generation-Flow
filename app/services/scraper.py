import re

import httpx
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CTA_PATTERN = re.compile(r"(book|contact|schedule|call|buy|shop|demo|start)", re.IGNORECASE)


async def scrape_website(url: str) -> dict:
    try:
        if not url.startswith("http"):
            url = f"https://{url}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

        headers = []
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if text:
                headers.append(text)
            if len(headers) >= 20:
                break

        content_snippets = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 20:
                content_snippets.append(text)
            if len(content_snippets) >= 20:
                break

        calls_to_action_found = []
        for link in soup.find_all("a"):
            text = link.get_text(strip=True)
            if text and CTA_PATTERN.search(text):
                calls_to_action_found.append(text)

        return {
            "url": url,
            "title": title,
            "description": description,
            "headers": headers,
            "content_snippets": content_snippets,
            "calls_to_action_found": calls_to_action_found,
        }
    except Exception as e:
        raise Exception(f"Failed to scrape website: {str(e)}")
