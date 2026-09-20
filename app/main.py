# Ana FastAPI uygulama dosyası, endpoint tanımlamaları.
from fastapi import FastAPI, HTTPException
from app.models.schemas import AnalizResponse
from app.services.trends_service import get_trend_data
from app.services.gemini_service import analyze_data
import time
import logging

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/analiz/{konu}", response_model=AnalizResponse)
async def analyze_trend(konu: str):
    total_start = time.time()
    
    try:
        # 1. Google Trends verisi çek
        logger.info(f"[{konu}] Fetching Google Trends data...")
        trends_start = time.time()
        data = get_trend_data(konu)
        trends_time = time.time() - trends_start
        logger.info(f"[{konu}] Google Trends done in {trends_time:.2f}s")
        
        # 2. Veriyi işle
        logger.info(f"[{konu}] Processing trend data...")
        process_start = time.time()
        # Data zaten temizlenmiş geliyor, ekstra işlem yok
        process_time = time.time() - process_start
        logger.info(f"[{konu}] Data processing done in {process_time:.2f}s")
        
        # 3. AI analizi
        logger.info(f"[{konu}] Sending data to AI...")
        ai_start = time.time()
        analysis = analyze_data(konu, data)
        ai_time = time.time() - ai_start
        logger.info(f"[{konu}] AI response received in {ai_time:.2f}s")
        
        # 4. Yanıtı hazırla
        logger.info(f"[{konu}] Generating result...")
        response_time = time.time() - process_start
        
        total_time = time.time() - total_start
        
        # Timing bilgilerini response'a ekle
        analysis["timing"] = {
            "google_trends_seconds": round(trends_time, 2),
            "data_processing_seconds": round(process_time, 2),
            "ai_request_seconds": round(ai_time, 2),
            "response_processing_seconds": round(response_time, 2),
            "total_seconds": round(total_time, 2)
        }
        
        logger.info(f"[{konu}] Complete in {total_time:.2f}s")
        
        return {"konu": konu, **analysis}
        
    except Exception as e:
        import traceback
        logger.error(f"[{konu}] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))