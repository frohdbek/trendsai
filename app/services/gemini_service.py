# Groq Cloud API kullanarak ham veriyi analiz eden servis (OpenAI uyumlu).
import httpx
import json
import re
from app.config import GROQ_API_KEY, GROQ_MODEL

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

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
        "risks": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3}
    },
    "required": ["opportunity_score", "demand_level", "trend_direction", "summary", "key_reasons", "opportunities", "risks"]
}

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
                iot_summary = f"Ortalama ilgi: {avg_val:.0f}/100, Maksimum: {max_val}/100, Veri noktasi: {len(values)} hafta"
    
    # Bolgesel ozet
    ibr_summary = ""
    if ibr and konu in ibr:
        regions = ibr[konu]
        if isinstance(regions, dict) and regions:
            top_regions = sorted(regions.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:5]
            ibr_summary = f"En yuksek ilgi: {', '.join([f'{r}({v})' for r, v in top_regions])}"
    
    # Top queries
    top_queries = []
    rising_queries = []
    for kw, qdata in rq.items():
        if isinstance(qdata, dict):
            top_queries.extend([item.get('query', '') for item in qdata.get('top', [])[:5]])
            rising_queries.extend([item.get('query', '') for item in qdata.get('rising', [])[:5]])
    
    # Related topics
    top_topics = []
    for kw, tdata in rt.items():
        if isinstance(tdata, dict):
            top_topics.extend([item.get('topic_title', '') for item in tdata.get('top', [])[:3]])
    
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

def _extract_json(content: str) -> dict:
    """AI yanıtından JSON'ı çıkarmayı dener - robust."""
    # Önce doğrudan parse et
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # JSON bloğunu bul (```json ... ``` veya { ... })
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Sadece { ... } bloğunu bul - en dıştaki parantez
    brace_match = re.search(r'(\{.*\})', content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Truncated JSON'ı onarmayı dene - son kapatma parantezini ekle
    if content.strip().startswith('{') and not content.strip().endswith('}'):
        # Eksik alanları tamamla
        fixed = content.strip() + '"}]}'
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract valid JSON from AI response")

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
            {"role": "system", "content": "You are a market analyst. Return ONLY valid JSON matching the exact schema provided. No markdown, no explanations, no extra text. Always complete the JSON object."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        
        if response.status_code != 200:
            print(f"Groq API Error: {response.status_code}")
            print(f"Response body: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # JSON parse et - robust extraction
        try:
            parsed = _extract_json(content)
            return parsed
        except (json.JSONDecodeError, ValueError) as e:
            # Safe logging - replace non-ascii
            safe_content = content.encode('ascii', 'replace').decode('ascii')
            print(f"JSON parse error: {e}")
            print(f"Raw content: {safe_content[:500]}")
            raise ValueError(f"AI returned invalid JSON: {e}")