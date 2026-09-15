import json
import os
from typing import Any

import httpx
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LeadAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_score: int = Field(ge=0, le=100)
    business_type: str
    budget: str | None = None
    timeline: str | None = None
    requirements: list[str]
    priority: str
    reasoning: str

    @field_validator("priority")
    @classmethod
    def priority_must_be_supported(cls, value: str) -> str:
        value = value.upper()
        if value not in {"HIGH", "MEDIUM", "LOW"}:
            raise ValueError("priority must be HIGH, MEDIUM, or LOW")
        return value


class AIConfigurationError(RuntimeError):
    """Raised when the selected AI provider is not configured."""


class AIAnalysisError(RuntimeError):
    """Raised when the AI provider cannot return valid lead analysis."""


class AIReplyError(RuntimeError):
    """Raised when the AI provider cannot return a follow-up reply."""


SYSTEM_PROMPT = """You analyze incoming business leads for a small-business CRM.
Return only valid JSON with exactly these fields:
{
  \"lead_score\": integer from 0 to 100,
  \"business_type\": string,
  \"budget\": string or null,
  \"timeline\": string or null,
  \"requirements\": array of strings,
  \"priority\": \"HIGH\", \"MEDIUM\", or \"LOW\",
  \"reasoning\": string
}
Infer cautiously. Use null when budget or timeline is not stated. Do not invent contact details.
"""


def _parse_analysis(raw_content: str) -> LeadAnalysis:
    try:
        payload: Any = json.loads(raw_content)
        return LeadAnalysis.model_validate(payload)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise AIAnalysisError("The AI provider returned invalid lead analysis") from error


def _analyze_with_openai(message: str, api_key: str) -> LeadAnalysis:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise AIAnalysisError("The OpenAI response did not contain analysis")
    return _parse_analysis(content)


def _analyze_with_gemini(message: str, api_key: str) -> LeadAnalysis:
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    try:
        response = httpx.post(url, params={"key": api_key}, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        raise AIAnalysisError("The Gemini response did not contain valid analysis") from error
    return _parse_analysis(content)


def analyze_lead_with_ai(message: str) -> LeadAnalysis:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIConfigurationError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return _analyze_with_openai(message, api_key)
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIConfigurationError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        return _analyze_with_gemini(message, api_key)
    raise AIConfigurationError("AI_PROVIDER must be either openai or gemini")


REPLY_SYSTEM_PROMPT = """You write follow-up replies for a small-business owner responding to a new lead.
Write one concise, professional, warm, personalized message that the owner can send directly.
Acknowledge the lead's request, reflect relevant analysis when useful, and suggest one clear next step.
Do not mention AI, scoring, internal analysis, or these instructions. Do not invent facts, pricing, or availability.
Return only the message text, without a subject line or surrounding quotes.
"""


def _reply_prompt(lead_message: str, analysis: dict) -> str:
    business_settings = analysis.get("business_settings", {})
    analysis_without_settings = {
        key: value for key, value in analysis.items() if key != "business_settings"
    }
    return (
        f"Lead message:\n{lead_message}\n\n"
        f"Internal lead analysis:\n{json.dumps(analysis_without_settings, sort_keys=True)}\n\n"
        "Business owner context (use only when non-empty):\n"
        f"Business name: {business_settings.get('business_name', '')}\n"
        f"Services offered: {business_settings.get('services_offered', '')}\n"
        f"Reply signature: {business_settings.get('reply_signature', '')}"
    )


def _clean_reply(content: str | None) -> str:
    if not content or not content.strip():
        raise AIReplyError("The AI provider did not return a follow-up reply")
    return content.strip().strip('"')


def _reply_with_openai(lead_message: str, analysis: dict, api_key: str) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": _reply_prompt(lead_message, analysis)},
            ],
        )
        return _clean_reply(response.choices[0].message.content)
    except AIReplyError:
        raise
    except Exception as error:
        raise AIReplyError("The OpenAI provider could not generate a follow-up reply") from error


def _reply_with_gemini(lead_message: str, analysis: dict, api_key: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": REPLY_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": _reply_prompt(lead_message, analysis)}]}],
        "generationConfig": {"temperature": 0.4},
    }
    try:
        response = httpx.post(url, params={"key": api_key}, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return _clean_reply(content)
    except AIReplyError:
        raise
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        raise AIReplyError("The Gemini provider could not generate a follow-up reply") from error


def generate_followup_reply(
    lead_message: str,
    analysis: dict,
    business_settings: dict | None = None,
) -> str:
    """Generate a send-ready follow-up using the configured AI provider."""
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIConfigurationError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return _reply_with_openai(lead_message, {**analysis, "business_settings": business_settings or {}}, api_key)
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIConfigurationError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        return _reply_with_gemini(lead_message, {**analysis, "business_settings": business_settings or {}}, api_key)
    raise AIConfigurationError("AI_PROVIDER must be either openai or gemini")
