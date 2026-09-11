import json
import time

from groq import Groq
from groq import APIConnectionError, APIStatusError

from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)
MODEL = "openai/gpt-oss-120b"

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 529}
MAX_RETRIES = 3


def _create_with_retry(*, system=None, messages, **kwargs):
    full_messages = list(messages)
    if system:
        full_messages = [{"role": "system", "content": system}] + full_messages

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=full_messages,
                **kwargs,
            )
            if not response.choices[0].message.content and attempt < MAX_RETRIES - 1:
                continue
            return response
        except APIStatusError as e:
            last_error = e
            status_code = getattr(e, "status_code", None)
            is_truncated_json = status_code == 400 and "json_validate_failed" in str(e)
            if (status_code in RETRYABLE_STATUS_CODES or is_truncated_json) and attempt < MAX_RETRIES - 1:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise
        except APIConnectionError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise
    raise last_error


def _get_text(response) -> str:
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from LLM")
    return content


def _extract_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[len("```json"):]
    elif content.startswith("```"):
        content = content[len("```"):]
    if content.endswith("```"):
        content = content[: -len("```")]
    return content.strip()


def _safe_json_loads(content: str) -> dict:
    cleaned = _extract_json(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        preview = cleaned[:200]
        raise ValueError(f"Failed to parse JSON response: {e}. Preview: {preview}")


def _about_us_block(additional_context: str) -> str:
    if not additional_context or not additional_context.strip():
        return ""
    return (
        "\n## About us (the person/agency making this offer)\n"
        f"{additional_context.strip()}\n\n"
        "When generating the solution/guidance/offer, actively incorporate specific, "
        "credible details from the 'About us' section above where relevant — e.g. named "
        "clients, case studies, industries served, or capabilities that strengthen this "
        "particular offer. Don't just treat it as background; use it to make the offer "
        "more concrete and credible. If no 'About us' context is provided, generate using "
        "only the business context as before.\n"
    )


def _format_problems(selected_problems: list) -> str:
    blocks = []
    for i, problem in enumerate(selected_problems, start=1):
        blocks.append(
            f"{i}. Title: {problem.get('title', '')}\n"
            f"   Why: {problem.get('why', '')}\n"
            f"   Evidence: {problem.get('evidence', '')}"
        )
    return "\n".join(blocks)


async def analyze_research(raw_scrape: dict) -> dict:
    system = (
        "You are a business research analyst. Given raw scraped website data, "
        "produce structured JSON describing the business. Only use facts actually "
        "present in the scraped data; never invent statistics or claims. Use empty "
        "values (empty string or empty list) if data is absent."
    )
    user = (
        "Here is the raw scraped website data:\n\n"
        f"{json.dumps(raw_scrape, indent=2)}\n\n"
        "Return a JSON object with exactly these keys: business_name, industry, "
        "products_services (list), target_audience, messaging, calls_to_action (list), "
        "observed_facts (list), potential_opportunities (list)."
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        response_format={"type": "json_object"},
        max_tokens=2000,
    )
    result = _safe_json_loads(_get_text(response))
    result["raw"] = raw_scrape
    return result


async def generate_problems(research_data: dict) -> dict:
    system = (
        "You are a business consultant. Given structured research data about a "
        "business, identify 3-5 plausible problems or opportunities worth addressing "
        "in a cold outreach email."
    )
    user = (
        "Here is the research data:\n\n"
        f"{json.dumps(research_data, indent=2)}\n\n"
        'Return JSON in this exact shape: {"problems": [{"title": "...", "why": "...", '
        '"evidence": "...", "confidence": "high/medium"}]}'
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        response_format={"type": "json_object"},
        max_tokens=1500,
    )
    return _safe_json_loads(_get_text(response))


async def suggest_solution(selected_problems: list, research_data: dict, additional_context: str = "") -> str:
    system = (
        "You are a strict business consultant. You may ONLY use information "
        "explicitly present in the verified research data, the selected problems, "
        "and the 'About us' context provided by the user (if any). Never invent "
        "client names, testimonials, results, guarantees, pricing, or any other "
        "claims that aren't present in those sources."
    )
    user = (
        "Selected problems:\n"
        f"{_format_problems(selected_problems)}\n\n"
        "Research data:\n"
        f"{json.dumps(research_data, indent=2)}\n"
        f"{_about_us_block(additional_context)}\n"
        "Write ONE concise, realistic solution that addresses ALL of the selected "
        "problems. 1-3 sentences. Plain text only, no markdown."
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=500,
    )
    return _get_text(response).strip()


TIMEFRAME_PLACEHOLDER = "Add only if you can genuinely commit to it."
GUARANTEE_PLACEHOLDER = "Add only if you actually provide one."

# Phrases the LLM sometimes substitutes for the required placeholder text.
# Treated as "no real value provided" even though they don't match verbatim.
_MISSING_VALUE_MARKERS = (
    "add only if",
    "not specified",
    "none proposed",
    "none provided",
    "not provided",
    "n/a",
    "none.",
    "no guarantee",
    "no timeframe",
    "not applicable",
)


def _is_missing_value(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized or normalized == "none":
        return True
    return any(marker in normalized for marker in _MISSING_VALUE_MARKERS)


async def guide_offer(selected_problems: list, initial_solution: str, research_data: dict, additional_context: str = "") -> dict:
    system = (
        "You are a strict sales and marketing expert. Never invent client names, "
        "testimonials, guarantees, pricing, statistics, percentages, or any other "
        "claims — including in the 'outcome' field — that aren't present in the "
        "research data or the 'About us' context provided by the user (if any). "
        "Only describe outcomes in qualitative terms unless a real number appears "
        "in the research data or the 'About us' context. Respond with valid JSON only."
    )
    user = (
        "Selected problems:\n"
        f"{_format_problems(selected_problems)}\n\n"
        f"Initial solution:\n{initial_solution}\n\n"
        "Research data:\n"
        f"{json.dumps(research_data, indent=2)}\n"
        f"{_about_us_block(additional_context)}\n"
        "Break the initial solution into a structured offer with keys: what, outcome, "
        "timeframe, guarantee.\n"
        "The 'outcome' field must describe the realistic result in qualitative terms "
        "only — do NOT invent percentages, statistics, or numeric metrics that are not "
        "explicitly present in the research data.\n"
        "If no real timeframe was given, set timeframe to EXACTLY this string, verbatim, "
        f'with no other text: "{TIMEFRAME_PLACEHOLDER}"\n'
        "If no real guarantee was given, set guarantee to EXACTLY this string, verbatim, "
        f'with no other text: "{GUARANTEE_PLACEHOLDER}"\n'
        "Do not paraphrase these two placeholder strings — copy them exactly when they apply.\n"
        'Return JSON like: {"what": "...", "outcome": "...", "timeframe": "...", "guarantee": "..."}'
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        response_format={"type": "json_object"},
        max_tokens=1200,
    )
    guidance = _safe_json_loads(_get_text(response))

    if _is_missing_value(guidance.get("timeframe", "")):
        guidance["timeframe"] = TIMEFRAME_PLACEHOLDER
    if _is_missing_value(guidance.get("guarantee", "")):
        guidance["guarantee"] = GUARANTEE_PLACEHOLDER

    return guidance


async def suggest_final_offer(selected_problems, research_data, initial_solution, guidance, additional_context="") -> str:
    timeframe = guidance.get("timeframe", "") or ""
    guarantee = guidance.get("guarantee", "") or ""

    timeframe_instruction = (
        "OMIT — no real timeframe was provided."
        if _is_missing_value(timeframe)
        else f"Include this timeframe: {timeframe}"
    )
    guarantee_instruction = (
        "OMIT — no real guarantee was provided."
        if _is_missing_value(guarantee)
        else f"Include this guarantee: {guarantee}"
    )

    system = (
        "You are a strict sales copywriter. The only permitted sources of information "
        "are the user's solution, the AI guidance, the verified research, and the "
        "'About us' context provided by the user (if any). Never invent claims, "
        "statistics, percentages, testimonials, or guarantees that are not explicitly "
        "present in those sources."
    )
    user = (
        "Selected problems:\n"
        f"{_format_problems(selected_problems)}\n\n"
        f"Initial solution:\n{initial_solution}\n\n"
        f"What: {guidance.get('what', '')}\n"
        f"Outcome: {guidance.get('outcome', '')}\n"
        f"Timeframe instruction: {timeframe_instruction}\n"
        f"Guarantee instruction: {guarantee_instruction}\n\n"
        "Research data:\n"
        f"{json.dumps(research_data, indent=2)}\n"
        f"{_about_us_block(additional_context)}\n"
        "Draft a 1-3 sentence final offer in first person (e.g. \"We'll ...\"), ready "
        "to paste into a cold outreach email. It must address ALL of the selected "
        "problems. If the outcome text above contains any specific percentages, "
        "statistics, or numeric guarantees not present in the research data, drop "
        "those numbers and restate the outcome qualitatively instead. Plain text "
        "only, no markdown."
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=600,
    )
    return _get_text(response).strip()


async def generate_outreach_email(research_data, selected_problems, final_offer, additional_instructions="", additional_context="") -> dict:
    system = (
        "You are an expert B2B copywriter. Write a personalized cold outreach email. "
        "Reference the specific business and actual research findings; weave in ALL "
        "of the selected problems; connect to the final offer; be concise and human; "
        "include a simple call to action; avoid generic sales language or invented "
        "claims. If the contact name is unknown, use \"Hi there,\" or \"Hi team,\"."
    )
    user = (
        "Research data:\n"
        f"{json.dumps(research_data, indent=2)}\n\n"
        "Selected problems:\n"
        f"{_format_problems(selected_problems)}\n\n"
        f"Final offer:\n{final_offer}\n\n"
        f"Additional context about our business (may be empty): {additional_context or 'None'}\n\n"
        f"Additional instructions: {additional_instructions or 'None'}\n\n"
        'Return JSON in this exact shape: {"subject": "...", "email": "..."}'
    )

    response = _create_with_retry(
        system=system,
        messages=[{"role": "user", "content": user}],
        response_format={"type": "json_object"},
        max_tokens=1200,
    )
    return _safe_json_loads(_get_text(response))
