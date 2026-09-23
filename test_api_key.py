# GROQ_API_KEY geçerliliğini test etmek için geçici script.
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key:
    print("HATA: .env dosyasında GROQ_API_KEY bulunamadı.")
    raise SystemExit(1)

print("API Key test ediliyor...")
try:
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Merhaba, çalışıyor musun?"}],
            "max_tokens": 20,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]
    print(f"BAŞARILI: API Key geçerli. Model yanıtı: {reply!r}")
except httpx.HTTPStatusError as e:
    print(f"HATA: API Key geçersiz veya istek reddedildi ({e.response.status_code}): {e.response.text}")
    raise SystemExit(1)
except httpx.HTTPError as e:
    print(f"HATA: Bağlantı sorunu: {e}")
    raise SystemExit(1)
