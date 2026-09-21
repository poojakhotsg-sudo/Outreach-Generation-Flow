import groq
from app.config import settings
import json
import time

client = groq.Groq(api_key=settings.GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 529}
_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.5


def _create_with_retry(*, system=None, messages, max_tokens, model=MODEL, **kwargs):
    """Retries Groq chat completion calls with exponential backoff on transient errors."""
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=full_messages,
                max_tokens=max_tokens,
                **kwargs,
            )
        except groq.APIStatusError as e:
            last_error = e
            if e.status_code not in _RETRYABLE_STATUS_CODES or attempt == _MAX_RETRIES:
                raise
        except groq.APIConnectionError as e:
            last_error = e
            if attempt == _MAX_RETRIES:
                raise
        time.sleep(_BASE_DELAY_SECONDS * (2 ** attempt))
    assert last_error is not None
    raise last_error


def _get_text(response) -> str:
    """Returns the message content from a Groq chat completion response."""
    content = response.choices[0].message.content
    if not content:
        raise ValueError("No text content found in Groq response.")
    return content


def _extract_json(content: str) -> str:
    """Strips markdown code fences from a Claude response."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
    return content


async def analyze_research(raw_scrape: dict) -> dict:
    prompt = f"""
    You are a business research analyst. Analyze the following raw data scraped from a business's website and produce a structured summary.

    Raw Scraped Data:
    {json.dumps(raw_scrape, indent=2)}

    Rules:
    1. Only extract or summarize information actually present in the raw data. NEVER invent facts, statistics, revenue, guarantees, or claims.
    2. "observed_facts" must be things directly stated or clearly evident in the scraped content.
    3. "potential_opportunities" are gaps or weaknesses you infer based on what's missing or unclear — label as inferences, not facts.
    4. If information for a field isn't available, use empty string, empty list, or "Unknown". Do not fabricate.
    5. Return strictly in this JSON format:
    {{
        "business_name": "Business name if identifiable, else Unknown",
        "industry": "Best guess at industry based on content, else Unknown",
        "products_services": ["list of products/services mentioned"],
        "target_audience": "Who the business appears to target",
        "messaging": "Summary of the site's core messaging/value proposition",
        "calls_to_action": ["CTAs found on the site"],
        "observed_facts": ["Specific facts directly observed from the scraped content"],
        "potential_opportunities": ["Inferred gaps or opportunities, clearly speculative"]
    }}
    Return ONLY valid JSON.
    """
    response = _create_with_retry(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    content = _extract_json(_get_text(response))
    structured = json.loads(content)
    structured["raw"] = raw_scrape
    return structured


async def generate_problems(research_data: dict) -> dict:
    prompt = f"""
    You are an expert business consultant. Analyze the following website research data and identify 3-5 potential problems or opportunities for improvement.

    Research Data:
    {json.dumps(research_data, indent=2)}

    Rules:
    1. Only use information actually found in the research. Do not invent facts.
    2. Identify problems based on observable gaps.
    3. Generate 3 to 5 meaningful problems. Do not stretch to 5 if only 3 are supported.
    4. Return strictly in this JSON format:
    {{
        "problems": [
            {{
                "title": "Short problem title",
                "why": "Brief explanation of why this is a problem",
                "evidence": "Specific evidence from the research",
                "confidence": "high/medium"
            }}
        ]
    }}
    Return ONLY valid JSON.
    """
    response = _create_with_retry(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    content = _extract_json(_get_text(response))
    return json.loads(content)


def _format_problems(selected_problems: list) -> str:
    blocks = []
    for idx, problem in enumerate(selected_problems, start=1):
        blocks.append(
            f"Problem {idx}:\n"
            f"Title: {problem.get('title')}\n"
            f"Why: {problem.get('why')}\n"
            f"Evidence: {problem.get('evidence')}"
        )
    return "\n\n".join(blocks)


async def suggest_solution(selected_problems: list, research_data: dict, additional_context: str = "") -> str:
    problem_count = len(selected_problems)

    context_instruction = f"\n\nAdditional Context About Us:\n{additional_context}\nYou MUST incorporate specific details from this context (company name, capabilities, industries, named clients if given) into your response where relevant. Do not ignore this section." if additional_context else ""

    system_prompt = (
        "You are a strict business consultant operating under hard content rules. "
        "You may ONLY use information explicitly present in the verified research provided. "
        "You must NEVER invent client names, logos, testimonials, quotes, case studies, "
        "results, outcomes, revenue figures, guarantees, timeframes, pricing, service names, "
        "CTA labels, or any social proof not found word-for-word in the research. "
        "If evidence is missing, say so and frame it as something the user should verify."
    ) + context_instruction

    user_prompt = f"""A user has selected {problem_count} problem(s) on a business website. Write one concise, realistic solution that addresses ALL of them.

Selected Problem(s) — address EVERY one of the {problem_count}:
{_format_problems(selected_problems)}

Verified Business Research (your ONLY permitted source of facts):
{json.dumps(research_data or {}, indent=2)}

Output rules:
1. Address ALL {problem_count} problems in one combined suggestion.
2. Base every fact on the verified research. If something is NOT confirmed, phrase it as: "You might consider [X] — verify this applies to your business first."
3. Do NOT invent client names, logos, testimonials, quotes, case studies, results, outcomes, pricing, or guarantees.
4. Write 1-3 sentences. Plain text. No markdown. No preamble."""

    response = _create_with_retry(
        model=MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return _get_text(response).strip()


async def guide_offer(selected_problems: list, initial_solution: str, research_data: dict = None, additional_context: str = "") -> dict:
    problem_count = len(selected_problems)

    context_instruction = f"\n\nAdditional Context About Us:\n{additional_context}\nYou MUST incorporate specific details from this context (company name, capabilities, industries, named clients if given) into your response where relevant. Do not ignore this section." if additional_context else ""

    system_prompt = (
        "You are a strict sales and marketing expert. "
        "You may ONLY use information explicitly present in the user's initial solution and the verified research. "
        "NEVER invent client names, testimonials, case studies, results, revenue figures, guarantees, timeframes, pricing, or service names. "
        "If evidence is missing for a field, use the exact placeholder string specified."
    ) + context_instruction

    user_prompt = f"""A user has selected {problem_count} problem(s) and provided an initial solution. Break it into a structured offer breakdown.

Selected Problem(s):
{_format_problems(selected_problems)}

User's Initial Solution (restate, do not expand):
{initial_solution}

Verified Business Research:
{json.dumps(research_data or {}, indent=2)}

Field rules:
1. "what": Restate what will be done using the user's own words. Must reflect ALL {problem_count} problems.
2. "outcome": One realistic, modest outcome grounded only in the solution and research. No invented metrics.
3. "timeframe": If the user's solution states a timeframe, restate it. Otherwise return exactly: "Add only if you can genuinely commit to it."
4. "guarantee": If the user's solution states a guarantee, restate it. Otherwise return exactly: "Add only if you actually provide one."

Return ONLY this JSON:
{{
    "what": "...",
    "outcome": "...",
    "timeframe": "...",
    "guarantee": "..."
}}"""

    response = _create_with_retry(
        model=MODEL,
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    content = _extract_json(_get_text(response))
    return json.loads(content)


async def suggest_final_offer(selected_problems: list, research_data: dict, initial_solution: str, guidance: dict, additional_context: str = "") -> str:
    problem_count = len(selected_problems)

    timeframe_val = guidance.get('timeframe', '')
    guarantee_val = guidance.get('guarantee', '')
    placeholder_phrases = ["add only if"]
    timeframe_is_placeholder = any(p in timeframe_val.lower() for p in placeholder_phrases)
    guarantee_is_placeholder = any(p in guarantee_val.lower() for p in placeholder_phrases)

    timeframe_instruction = (
        "OMIT — no real timeframe was provided."
        if timeframe_is_placeholder
        else f'Include this timeframe: "{timeframe_val}"'
    )
    guarantee_instruction = (
        "OMIT — no real guarantee was provided."
        if guarantee_is_placeholder
        else f'Include this guarantee: "{guarantee_val}"'
    )

    context_instruction = f"\n\nAdditional Context About Us:\n{additional_context}\nYou MUST incorporate specific details from this context (company name, capabilities, industries, named clients if given) into your response where relevant. Do not ignore this section." if additional_context else ""

    system_prompt = (
        "You are a strict sales copywriter. "
        "Your only permitted sources are: (1) the user's initial solution, (2) the AI guidance derived from it, "
        "and (3) the verified business research. "
        "NEVER invent client names, logos, testimonials, case studies, industry verticals, results, revenue figures, "
        "percentage improvements, pricing, CTA labels, or guarantees unless in the sources. "
        "Base this ONLY on the facts, claims, and deliverables stated in the Offer Guidance provided. Do not invent new deliverables, technologies, statistics, or claims that are not already present there. "
        "CRITICALLY: frame every deliverable as something you will DO or BUILD for the client (e.g. 'we'll create a case-study section', 'we'll help you build tiered pricing'), never as something you already possess and are ready to hand over (avoid phrasing like 'here is our case study', 'I'll send you the materials', 'you'll get our PDF'). The client currently lacks these assets, which is why this offer exists."
    ) + context_instruction

    user_prompt = f"""Draft a 1-4 sentence final offer for the user to drop into a cold email.

Selected Problem(s) — the offer MUST address ALL {problem_count}:
{_format_problems(selected_problems)}

Verified Business Research:
{json.dumps(research_data or {}, indent=2)}

User's Initial Solution:
{initial_solution}

AI Guidance (YOUR SINGLE SOURCE OF TRUTH FOR THE OFFER):
What: {guidance.get('what', '')}
Outcome: {guidance.get('outcome', '')}
Timeframe: {timeframe_instruction}
Guarantee: {guarantee_instruction}

Output rules:
1. First person (e.g. "We'll ..."), ready to paste into an email.
2. Address all {problem_count} problems coherently.
3. Follow the Timeframe and Guarantee instructions exactly.
4. STRICTLY ground all claims in the AI Guidance.
5. 1-4 sentences. Plain text. No markdown. No preamble."""

    response = _create_with_retry(
        model=MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return _get_text(response).strip()


async def generate_outreach_email(research_data: dict, selected_problems: list, final_offer: str, additional_instructions: str = "", additional_context: str = "") -> dict:
    problems_summary = "\n".join(
        f"- {p.get('title')} - {p.get('why')}" for p in selected_problems
    )
    prompt = f"""
    You are an expert B2B copywriter. Write a personalized cold email based strictly on:

    Business Research: {json.dumps(research_data, indent=2)}
    Selected Problem(s):
    {problems_summary}
    Final Offer: {final_offer}
    Additional Instructions: {additional_instructions}
    Additional Context About Us: {additional_context}

    Rules:
    1. Reference the specific business and something actually discovered in the research.
    2. Naturally bring up the selected problem(s). Weave all of them in — do not omit any.
    3. Connect the problem(s) to the user's final offer.
    4. Be concise, sound natural and human.
    5. The Call to Action MUST invite a conversation or call to discuss the work (e.g. 'would you be open to a brief call next week?'). Do NOT imply materials are ready to send immediately unless the offer genuinely involves handing over a free existing asset (like an audit or template).
    6. Do NOT use generic sales language, fake personalization, unsupported claims, or invented guarantees unless in the Final Offer.
    7. If the contact name is unknown, use "Hi there," or "Hi team,". Do not invent a name.
    8. If Additional Context About Us is provided, you MUST incorporate specific details from it (company name, capabilities, etc) into your response where relevant. Do not ignore it.
    9. Base this ONLY on the Final Offer and Selected Problems. Do not invent new deliverables, technologies, statistics, or claims.
    10. CRITICALLY: frame deliverables as things we will DO or BUILD for the client, not things we already possess to hand over.

    Return strictly as JSON:
    {{
        "subject": "Compelling subject line",
        "email": "The full email body"
    }}
    Return ONLY valid JSON.
    """
    response = _create_with_retry(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    content = _extract_json(_get_text(response))
    return json.loads(content)
