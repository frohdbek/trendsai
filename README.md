# TrendsAI — Trend Analiz Uygulaması
 
Bir konu girin, Google Trends verilerini ve yapay zeka destekli pazar analizini birlikte alın. TrendsAI, girilen konunun Türkiye'deki arama ilgisini Google Trends'ten çeker, bu veriyi Groq üzerinden çalışan bir LLM ile yorumlayıp fırsat puanı, talep seviyesi, trend yönü, riskler ve iş fikirleri üretir.
 
🔗 **Canlı demo:** [trendsai.com.tr](https://trendsai.com.tr)
 
---
 
## İçindekiler
 
- [Nasıl çalışır](#nasıl-çalışır)
- [Teknoloji yığını](#teknoloji-yığını)
- [Proje yapısı](#proje-yapısı)
- [Kurulum](#kurulum)
- [Ortam değişkenleri](#ortam-değişkenleri)
- [Çalıştırma](#çalıştırma)
- [API](#api)
- [Barındırma mimarisi](#barındırma-mimarisi)
- [Bilinen kısıtlar](#bilinen-kısıtlar)
- [Lisans](#lisans)
---
 
## Nasıl çalışır
 
1. Kullanıcı arayüze bir konu (örn. "bitcoin", "elektrikli araçlar") girer.
2. Backend, `pytrends` ile Google Trends'ten son 12 aylık ilgi verisini, bölgesel dağılımı ve ilişkili aramaları çeker.
3. Bu veri özetlenip Groq'ta çalışan bir LLM'e gönderilir; model veriyi yorumlayıp yapılandırılmış bir JSON döner.
4. Sonuç; fırsat puanı, talep seviyesi, trend yönü, özet, nedenler, fırsatlar ve riskler olarak arayüzde gösterilir.
## Teknoloji yığını
 
| Katman | Teknoloji |
|---|---|
| Backend | FastAPI (Python) |
| Sunucu | Uvicorn |
| Trend verisi | pytrends (Google Trends, resmi olmayan kütüphane) |
| Yapay zeka | Groq Cloud API (OpenAI uyumlu, varsayılan model: `openai/gpt-oss-20b`) |
| Frontend | Tek dosyalık vanilla HTML/CSS/JS |
| Barındırma | Backend: Raspberry Pi (ev sunucusu) · Frontend: Render (Static Site) |
| Domain / DNS / SSL | Cloudflare + Cloudflare Tunnel |
 
## Proje yapısı
 
```
trendsai/
├── app/
│   ├── main.py                # FastAPI giriş noktası, endpoint tanımları
│   ├── config.py               # Ortam değişkenlerini okuyan konfigürasyon modülü
│   ├── models/
│   │   └── schemas.py          # Pydantic istek/yanıt modelleri
│   └── services/
│       ├── trends_service.py   # Google Trends veri çekme
│       └── groq_service.py     # Groq (LLM) analizi ve JSON çıkarımı
├── frontend/
│   └── index.html              # Minimal web arayüzü
├── start.bat                   # Windows batch başlatıcı
├── start.ps1                   # PowerShell başlatıcı
├── requirements.txt
├── .env.example                 # Örnek ortam değişkenleri
└── .env                          # Gerçek anahtarlar (git'e dahil edilmez)
```
 
## Kurulum
 
```bash
python -m venv venv
 
# Windows (PowerShell)
venv\Scripts\Activate.ps1
 
# macOS / Linux
source venv/bin/activate
 
python -m pip install -r requirements.txt
```
 
`.env.example` dosyasını `.env` olarak kopyalayın ve en azından `GROQ_API_KEY` değerini girin:
 
```bash
cp .env.example .env   # Windows: Copy-Item .env.example .env
```
 
## Ortam değişkenleri
 
| Değişken | Zorunlu | Varsayılan | Açıklama |
|---|---|---|---|
| `GROQ_API_KEY` | Evet | — | [console.groq.com/keys](https://console.groq.com/keys) adresinden alınan API anahtarı. Tanımlı değilse uygulama açılışta hata verir. |
| `GROQ_MODEL` | Hayır | `openai/gpt-oss-20b` | Kullanılacak Groq modeli. Güncel liste: [console.groq.com/docs/models](https://console.groq.com/docs/models) |
| `ALLOWED_ORIGINS` | Hayır | `http://localhost:3000,http://127.0.0.1:3000` | CORS için izin verilen, virgülle ayrılmış frontend adresleri. Üretimde gerçek domain(ler)inizi girin. |
| `MAX_KONU_LENGTH` | Hayır | `100` | Tek bir istekte kabul edilecek maksimum "konu" karakter uzunluğu, kötüye kullanımı sınırlamak için. |
| `LOG_LEVEL` | Hayır | `INFO` | Loglama seviyesi. |
 
## Çalıştırma
 
### Seçenek 1 — Otomatik (Windows)
 
`start.bat` veya `start.ps1` dosyasına çift tıklayın. Backend `http://localhost:8000`, frontend `http://localhost:3000` adresinde açılır.
 
### Seçenek 2 — Manuel
 
**Terminal 1 — Backend:**
```bash
uvicorn app.main:app --reload --port 8000
```
 
**Terminal 2 — Frontend:**
```bash
cd frontend
python -m http.server 3000
```
 
Sonra tarayıcıda `http://localhost:3000` adresini açın.
 
### Seçenek 3 — Sadece API
 
```bash
uvicorn app.main:app --reload
```
 
İnteraktif API dokümantasyonu: `http://localhost:8000/docs`
 
## API
 
```
GET /analiz/{konu}
GET /health
```
 
**Örnek yanıt:**
 
```json
{
  "konu": "bitcoin",
  "opportunity_score": 70,
  "demand_level": "high",
  "trend_direction": "rising",
  "summary": "Bitcoin interest moderate nationwide with spikes in key provinces; rising queries show growing demand; opportunities in localized payment solutions, education, and crypto exchange services.",
  "key_reasons": [
    "Average interest 42/100 indicates solid demand",
    "Rising queries like 'how to buy bitcoin safely' show increasing user intent",
    "High interest in major provinces like Istanbul and Kayseri suggests regional adoption potential"
  ],
  "opportunities": [
    "Launch a Turkish-language crypto education platform targeting high-interest provinces",
    "Partner with local banks to offer Bitcoin payment gateways",
    "Develop a localized crypto exchange with Turkish Lira support"
  ],
  "risks": [
    "Regulatory uncertainty in Turkey",
    "Volatility of Bitcoin price may deter users",
    "Competition from established exchanges"
  ],
  "timing": {
    "google_trends_seconds": 10.04,
    "data_processing_seconds": 0.0,
    "ai_request_seconds": 2.43,
    "response_processing_seconds": 0.0,
    "total_seconds": 12.47
  }
}
```
 
## Barındırma mimarisi
 
```
Kullanıcı
   │
   ├─ https://trendsai.com.tr ───────► Render (Static Site) — frontend
   │
   └─ https://api.trendsai.com.tr ───► Cloudflare Tunnel ───► Raspberry Pi — backend (FastAPI)
```
 
Domain Cloudflare üzerinden yönetiliyor, DNS ve SSL Cloudflare tarafından otomatik sağlanıyor. Backend, bulut sunucuları yerine bilinçli olarak bir Raspberry Pi'de barındırılıyor (bkz. Bilinen kısıtlar).
 
## Bilinen kısıtlar
 
- **Google Trends resmi bir API değil.** `pytrends`, Google Trends'in web arayüzünü kullanır. Veri merkezi (bulut) IP'lerinden gelen yoğun/otomatik trafik Google tarafından sık sık `429 Too Many Requests` ile engellenir. Bu yüzden backend, IP itibarı daha "temiz" olan bir ev sunucusunda (Raspberry Pi) çalıştırılıyor.
- **Bu proje bir hobi/demo çalışmasıdır**, üretim/iş kritik bir servis değildir. Beklenmedik kesintiler (elektrik/internet kesintisi, Groq/Google tarafındaki geçici kısıtlamalar) olabilir.
- Groq'un ücretsiz katmanı kullanılıyor; yoğun kullanımda hız sınırına (rate limit) takılabilir.
## Lisans
 
MIT
