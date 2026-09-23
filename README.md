# Trend Analiz Uygulaması

Bu uygulama, Google Trends verilerini çeker ve Gemini AI kullanarak analiz eder.

## Kurulum

1. **Bağımlılıkları yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **`.env` dosyası oluşturun** (`.env.example`'dan kopyalayarak) ve API anahtarlarınızı ekleyin:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```

## Çalıştırma

### Seçenek 1: Otomatik (Windows) - Önerilen
**`start.bat`** veya **`start.ps1`** dosyalarını çift tıklayarak çalıştırın.
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Seçenek 2: Manuel

**Terminal 1 - Backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 3000
```

### Seçenek 3: Sadece API (Backend)
```bash
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

## Kullanım

1. Frontend'i açın: **http://localhost:3000**
2. Bir konu girin (örn: "yapay zeka", "elektrikli araçlar", "kripto para")
3. "Analiz Et" butonuna tıklayın
4. Sonuçları görüntüleyin:
   - Fırsat Puanı (0-100)
   - Talep Seviyesi & Trend Yönü
   - AI Özeti
   - Ana Nedenler, Fırsat Fikirleri, Riskler
   - Performans metrikleri

## API Endpoint

```
GET /analiz/{konu}
```

**Yanıt örneği:**
```json
{
  "konu": "yapay zeka",
  "opportunity_score": 85,
  "demand_level": "very_high",
  "trend_direction": "rising",
  "summary": "Yapay zeka alanı hızla büyüyen bir pazar...",
  "key_reasons": ["Arama ilgisi %200 arttı", "Yatırım fonları akını devam ediyor"],
  "opportunities": ["AI araçları geliştirme", "Eğitim platformu kurma"],
  "risks": ["Rekabet yoğun", "Teknoloji hızla değişiyor"],
  "timing": {
    "google_trends_seconds": 1.23,
    "data_processing_seconds": 0.05,
    "ai_request_seconds": 3.45,
    "response_processing_seconds": 0.02,
    "total_seconds": 4.75
  }
}
```

## Proje Yapısı

```
trend-analiz-app/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Konfigürasyon
│   ├── models/
│   │   └── schemas.py       # Pydantic modelleri
│   └── services/
│       ├── trends_service.py # Google Trends veri çekme
│       └── groq_service.py   # Groq (LLM) analizi
├── frontend/
│   └── index.html           # Minimal web arayüzü
├── start.bat                # Windows batch başlatıcı
├── start.ps1                # PowerShell başlatıcı
├── requirements.txt
└── .env                     # API keys (gitignored)
```