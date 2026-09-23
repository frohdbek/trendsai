# Ana FastAPI uygulama dosyası, endpoint tanımlamaları.
import logging
import time
from functools import partial

from fastapi import FastAPI, HTTPException, Path
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, MAX_KONU_LENGTH
from app.models.schemas import AnalizResponse
from app.services.groq_service import analyze_data
from app.services.trends_service import get_trend_data

logger = logging.getLogger(__name__)

app = FastAPI(title="TrendsAI")

# CORS ayarları - Frontend'in API'ye erişmesi için.
# Origin listesi app/config.py -> ALLOWED_ORIGINS üzerinden .env ile yönetilir.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/analiz/{konu}", response_model=AnalizResponse)
async def analyze_trend(
    konu: str = Path(..., min_length=1, max_length=MAX_KONU_LENGTH),
):
    konu = konu.strip()
    if not konu:
        raise HTTPException(status_code=422, detail="konu boş olamaz")

    total_start = time.time()

    try:
        # 1. Google Trends verisi çek (bloklayıcı çağrı - thread'e devredilir
        # ki event loop diğer istekleri işlemeye devam edebilsin)
        logger.info("[%s] Fetching Google Trends data...", konu)
        trends_start = time.time()
        data = await run_in_threadpool(partial(get_trend_data, konu))
        trends_time = time.time() - trends_start
        logger.info("[%s] Google Trends done in %.2fs", konu, trends_time)

        # 2. AI analizi (bu da bloklayıcı bir HTTP çağrısı - aynı şekilde thread'e devredilir)
        logger.info("[%s] Sending data to AI...", konu)
        ai_start = time.time()
        analysis = await run_in_threadpool(partial(analyze_data, konu, data))
        ai_time = time.time() - ai_start
        logger.info("[%s] AI response received in %.2fs", konu, ai_time)

        # 3. Yanıtı hazırla
        response_start = time.time()
        response_time = time.time() - response_start
        total_time = time.time() - total_start

        analysis["timing"] = {
            "google_trends_seconds": round(trends_time, 2),
            "data_processing_seconds": 0.0,  # data zaten temizlenmiş geliyor, ekstra işlem yok
            "ai_request_seconds": round(ai_time, 2),
            "response_processing_seconds": round(response_time, 2),
            "total_seconds": round(total_time, 2),
        }

        logger.info("[%s] Complete in %.2fs", konu, total_time)

        return {"konu": konu, **analysis}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[%s] Error while analyzing trend", konu)
        raise HTTPException(status_code=500, detail=str(e)) from e
