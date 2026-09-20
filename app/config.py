# Uygulama konfigürasyonunu yönetir, ortam değişkenlerini yükler.
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY ortam değişkeni bulunamadı!")