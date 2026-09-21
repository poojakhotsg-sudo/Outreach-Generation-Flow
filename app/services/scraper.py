import httpx
from bs4 import BeautifulSoup
import re


async def scrape_website(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string if soup.title else ""
            meta_desc = ""
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                meta_desc = desc_tag.get('content', '')

            headers_text = []
            for tag in ['h1', 'h2', 'h3']:
                for header in soup.find_all(tag):
                    text = header.get_text(strip=True)
                    if text:
                        headers_text.append(text)

            paragraphs_text = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 20:
                    paragraphs_text.append(text)

            links = []
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                if text and len(text) > 2:
                    links.append({"text": text, "href": a['href']})

            return {
                "url": url,
                "title": title,
                "description": meta_desc,
                "headers": headers_text[:20],
                "content_snippets": paragraphs_text[:20],
                "calls_to_action_found": [
                    link for link in links
                    if re.search(r'(book|contact|schedule|call|buy|shop|demo|start)', link['text'].lower())
                ][:20]
            }

    except Exception as e:
        raise Exception(f"Failed to scrape website: {str(e)}")
