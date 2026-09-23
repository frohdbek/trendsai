# Uygulama konfigürasyonunu yönetir, ortam değişkenlerini yükler.
import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# NOT: Groq'un desteklediği model listesi zaman içinde değişebilir.
# Güncel/desteklenen modeller için https://console.groq.com/docs/models adresini kontrol edin.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY ortam değişkeni bulunamadı! "
        ".env dosyanızda GROQ_API_KEY=... tanımlı olduğundan emin olun."
    )

# CORS için izin verilen originler. Prod'da "*" yerine gerçek frontend
# domain(ler)ini kullanın, virgülle ayırarak: "https://a.com,https://b.com"
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if o.strip()
]

# İstek başına maksimum konu uzunluğu (kötüye kullanımı / aşırı büyük
# promptları önlemek için).
MAX_KONU_LENGTH = int(os.getenv("MAX_KONU_LENGTH", "100"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
