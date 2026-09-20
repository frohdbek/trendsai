# API Key geçerliliğini test etmek için geçici script.
import os
from dotenv import load_dotenv
from google.genai import Client

# .env dosyasını yükle
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("HATA: .env dosyasında GEMINI_API_KEY bulunamadı.")
    exit(1)

try:
    print("API Key test ediliyor...")
    client = Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents="Merhaba, çalışıyor musun?",
    )
    print("BAŞARILI: API Key geçerli.")
except Exception as e:
    print(f"HATA: API Key geçersiz veya bağlantı sorunu: {e}")
    exit(1)
