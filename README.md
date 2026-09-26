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
- [Kalıcılık (systemd)](#kalıcılık-systemd)
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
| Frontend | Tek dosyalık vanilla HTML/CSS/JS, Python `http.server` ile sunuluyor |
| Barındırma | Backend + Frontend: Raspberry Pi (ev sunucusu), systemd servisleri olarak çalışıyor |
| Domain / DNS / SSL / Tünel | Cloudflare + Cloudflare Tunnel (`cloudflared`) |

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
├── start.bat                   # Windows batch başlatıcı (yerel geliştirme)
├── start.ps1                   # PowerShell başlatıcı (yerel geliştirme)
├── requirements.txt
├── .env.example                 # Örnek ortam değişkenleri
└── .env                          # Gerçek anahtarlar (git'e dahil edilmez)
```

## Kurulum

```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux / Raspberry Pi
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
| `ALLOWED_ORIGINS` | Hayır | `http://localhost:3000,http://127.0.0.1:3000` | CORS için izin verilen, virgülle ayrılmış frontend adresleri. Üretimde: `https://trendsai.com.tr,https://www.trendsai.com.tr` |
| `MAX_KONU_LENGTH` | Hayır | `100` | Tek bir istekte kabul edilecek maksimum "konu" karakter uzunluğu, kötüye kullanımı sınırlamak için. |
| `LOG_LEVEL` | Hayır | `INFO` | Loglama seviyesi. |

## Çalıştırma

Aşağıdaki yöntemler yerel geliştirme/test içindir. Üretimde (Raspberry Pi) servisler systemd ile otomatik çalışır, bkz. [Kalıcılık (systemd)](#kalıcılık-systemd).

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

Hem backend hem frontend, **tek bir Raspberry Pi** üzerinde çalışır ve **Cloudflare Tunnel** ile dışarıya açılır. Pi'ye giden port yönlendirmesi (port forwarding) yapılmaz; Pi, Cloudflare'e kendisi dışarı doğru bağlanır.

```
Kullanıcı
   │
   ├─ https://trendsai.com.tr      ─┐
   ├─ https://www.trendsai.com.tr  ─┼─► Cloudflare Tunnel ─► Raspberry Pi :3000 (frontend, http.server)
   │                                │
   └─ https://api.trendsai.com.tr  ─┴─► Cloudflare Tunnel ─► Raspberry Pi :8000 (backend, FastAPI/uvicorn)
```

Domain, DNS ve SSL sertifikası tamamen Cloudflare tarafından yönetilir/otomatik sağlanır. Backend, bulut sunucuları yerine bilinçli olarak bir Raspberry Pi'de (ev IP'si) barındırılıyor — bkz. [Bilinen kısıtlar](#bilinen-kısıtlar).

## Kalıcılık (systemd)

Pi'de üç ayrı systemd servisi çalışır; hepsi açılışta otomatik başlar (`enable`) ve çökerse kendini yeniden başlatır (`Restart=always`):

| Servis | Görevi |
|---|---|
| `cloudflared` | Cloudflare Tunnel istemcisi, `trendsai.com.tr` / `www.trendsai.com.tr` / `api.trendsai.com.tr` trafiğini Pi'ye taşır |
| `trendsai-backend` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| `trendsai-frontend` | `python3 -m http.server 3000 --bind 0.0.0.0` (`frontend/` klasöründe) |

Durum kontrolü:
```bash
sudo systemctl status cloudflared trendsai-backend trendsai-frontend --no-pager
```

Kod veya `.env` değişikliğinden sonra ilgili servisi yeniden başlatmak gerekir (otomatik algılanmaz):
```bash
sudo systemctl restart trendsai-backend
sudo systemctl restart trendsai-frontend
```

Canlı log takibi:
```bash
journalctl -u trendsai-backend -f
```

Bu kurulum, Pi'nin elektrik/ağ kesintisi sonrası yeniden başlamasında (`reboot`) elle müdahale gerekmeden kendiliğinden ayağa kalkacak şekilde test edilmiştir.

## Bilinen kısıtlar

- **Google Trends resmi bir API değil.** `pytrends`, Google Trends'in web arayüzünü kullanır. Veri merkezi (bulut) IP'lerinden gelen yoğun/otomatik trafik Google tarafından sık sık `429 Too Many Requests` ile engellenir. Bu yüzden backend, IP itibarı daha "temiz" olan bir ev sunucusunda (Raspberry Pi) çalıştırılıyor.
- **Groq'un ücretsiz katmanı kullanılıyor**; bazı isteklerde model geçici olarak geçersiz/eksik JSON üretebilir, bu da Groq API'sinden ara sıra `400 Bad Request` alınmasına yol açabilir. Kısa bir süre sonra tekrar denemek genellikle sorunu çözer.
- **Bu proje bir hobi/demo çalışmasıdır**, üretim/iş kritik bir servis değildir. Beklenmedik kesintiler (elektrik/internet kesintisi, Groq/Google tarafındaki geçici kısıtlamalar) olabilir.
- Fırsat puanı yalnızca Google Trends arama hacmine dayanır; çok niş/yeni konularda arama hacmi ölçülemediği için düşük puan çıkabilir, bu gerçek pazar potansiyelini tam yansıtmayabilir.

## Lisans

MIT
