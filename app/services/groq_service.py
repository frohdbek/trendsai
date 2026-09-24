# Groq Cloud API kullanarak ham veriyi analiz eden servis (OpenAI uyumlu).
import json
import logging
import re
from typing import Optional

import httpx

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 2

# JSON şema tanımı
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "opportunity_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "demand_level": {"type": "string", "enum": ["very_high", "high", "medium", "low", "very_low"]},
        "trend_direction": {"type": "string", "enum": ["rising", "stable", "falling", "volatile"]},
        "summary": {"type": "string", "maxLength": 200},
        "key_reasons": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3},
        "opportunities": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3},
        "risks": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
    },
    "required": [
        "opportunity_score",
        "demand_level",
        "trend_direction",
        "summary",
        "key_reasons",
        "opportunities",
        "risks",
    ],
}

REQUIRED_FIELDS = set(RESPONSE_SCHEMA["required"])


def _build_prompt(konu: str, data: dict) -> str:
    """AI için optimize edilmiş, küçük prompt oluştur."""
    iot = data.get("interest_over_time", {})
    ibr = data.get("interest_by_region", {})
    rq = data.get("related_queries", {})
    rt = data.get("related_topics", {})

    # Interest over time özeti
    iot_summary = ""
    if iot and konu in iot:
        values = list(iot[konu].values()) if isinstance(iot[konu], dict) else []
        if values:
            valid_vals = [v for v in values if isinstance(v, (int, float))]
            if valid_vals:
                avg_val = sum(valid_vals) / len(valid_vals)
                max_val = max(valid_vals)
                iot_summary = (
                    f"Ortalama ilgi: {avg_val:.0f}/100, Maksimum: {max_val}/100, "
                    f"Veri noktasi: {len(values)} hafta"
                )

    # Bolgesel ozet
    ibr_summary = ""
    if ibr and konu in ibr:
        regions = ibr[konu]
        if isinstance(regions, dict) and regions:
            top_regions = sorted(
                regions.items(),
                key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                reverse=True,
            )[:5]
            ibr_summary = f"En yuksek ilgi: {', '.join(f'{r}({v})' for r, v in top_regions)}"

    # Top queries
    top_queries = []
    rising_queries = []
    for _, qdata in rq.items():
        if isinstance(qdata, dict):
            top_queries.extend(item.get("query", "") for item in qdata.get("top", [])[:5])
            rising_queries.extend(item.get("query", "") for item in qdata.get("rising", [])[:5])

    # Related topics
    top_topics = []
    for _, tdata in rt.items():
        if isinstance(tdata, dict):
            top_topics.extend(item.get("topic_title", "") for item in tdata.get("top", [])[:3])

    prompt = f"""Analyze Google Trends data for "{konu}" (Turkey, last 12 months).

DATA SUMMARY:
{iot_summary}
{ibr_summary}

TOP RELATED QUERIES: {', '.join(top_queries[:10])}
RISING QUERIES: {', '.join(rising_queries[:10])}
TOP TOPICS: {', '.join(top_topics[:5])}

Return ONLY valid JSON matching this schema:
{json.dumps(RESPONSE_SCHEMA, indent=2)}

Rules:
- opportunity_score: 0-100 based on demand + growth potential
- demand_level: very_high/high/medium/low/very_low
- trend_direction: rising/stable/falling/volatile
- summary: max 200 chars, business-focused insight
- key_reasons: 2-3 specific data-driven reasons
- opportunities: 2-3 actionable business ideas
- risks: 1-3 potential risks

Output ONLY the JSON object, no markdown, no extra text."""

    return prompt


def _extract_balanced_json(content: str) -> Optional[str]:
    """İlk '{' karakterinden başlayıp parantez dengesine göre eşleşen
    kapanış parantezini bularak en dıştaki JSON nesnesini çıkarır.
    Yarım kalmış (truncated) yanıtlara karşı bracket-matching kullanır -
    içerik sonuna kör bir sonek eklemekten daha güvenilirdir."""
    start = content.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(content)):
        ch = content[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[start : i + 1]

    return None


def _extract_json(content: str) -> dict:
    """AI yanıtından JSON'ı çıkarmayı dener - birden çok stratejiyle."""
    # 1. Doğrudan parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. ```json ... ``` bloğu
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Parantez dengesine göre en dıştaki { ... } bloğu (truncated
    # yanıtlarda da güvenilir şekilde çalışır)
    balanced = _extract_balanced_json(content)
    if balanced:
        try:
            return json.loads(balanced)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from AI response")


def _validate_shape(parsed: dict) -> None:
    """AI'dan gelen JSON'da beklenen alanların var olduğunu doğrular.
    Eksik alan varsa erken ve anlaşılır bir hata fırlatır."""
    missing = REQUIRED_FIELDS - parsed.keys()
    if missing:
        raise ValueError(f"AI response missing required fields: {sorted(missing)}")


def analyze_data(konu: str, data: dict) -> dict:
    """Trends verilerini analiz edip structured JSON döndürür."""
    prompt = _build_prompt(konu, data)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a market analyst. Return ONLY valid JSON matching the "
                    "exact schema provided. No markdown, no explanations, no extra "
                    "text. Always complete the JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
	"response_format": {"type": "json_object"},
    }

    last_error: Optional[Exception] = None

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            except httpx.TransportError as e:
                last_error = e
                logger.warning("[%s] Groq request failed (attempt %d/%d): %s", konu, attempt, MAX_RETRIES, e)
                continue

            if response.status_code != 200:
                logger.error(
                    "[%s] Groq API error (attempt %d/%d): status=%s body=%s",
                    konu, attempt, MAX_RETRIES, response.status_code, response.text,
                )
                last_error = httpx.HTTPStatusError(
                    f"Groq API returned {response.status_code}", request=response.request, response=response,
                )
                # 4xx (kota/yetki/istek hatası) tekrar denemekle düzelmez
                if response.status_code < 500:
                    response.raise_for_status()
                continue

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            try:
                parsed = _extract_json(content)
                _validate_shape(parsed)
                return parsed
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.error("[%s] JSON parse error (attempt %d/%d): %s", konu, attempt, MAX_RETRIES, e)
                logger.debug("[%s] Raw AI content: %s", konu, content[:500])
                continue

    raise ValueError(f"AI returned invalid or unusable response after {MAX_RETRIES} attempt(s): {last_error}")
