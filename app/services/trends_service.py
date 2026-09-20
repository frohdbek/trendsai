# Pytrends kullanarak Google Trends verilerini çeken servis.
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
from time import sleep
import time
from datetime import datetime, timedelta
from threading import Lock

# In-memory cache with TTL
_CACHE = {}
_CACHE_LOCK = Lock()
CACHE_TTL_SECONDS = 3600  # 1 saat

def _get_cached(konu: str):
    """Cache'den veri al (varsa ve geçerliyse)."""
    with _CACHE_LOCK:
        if konu in _CACHE:
            cached_time, cached_data = _CACHE[konu]
            if datetime.now() - cached_time < timedelta(seconds=CACHE_TTL_SECONDS):
                print(f"[CACHE HIT] {konu} - {round((datetime.now() - cached_time).total_seconds())}s ago")
                # Cache time bilgisini ekle
                cached_data["_meta"]["cached"] = True
                cached_data["_meta"]["cache_age_seconds"] = round((datetime.now() - cached_time).total_seconds())
                return cached_data
    return None

def _set_cache(konu: str, data: dict):
    """Cache'e veri yaz."""
    with _CACHE_LOCK:
        _CACHE[konu] = (datetime.now(), data)

def get_trend_data(konu: str) -> dict:
    """Google Trends verilerini çeker ve özetler (cache ile)."""
    
    # 1. Cache kontrolü
    cached = _get_cached(konu)
    if cached:
        return cached
    
    print(f"[CACHE MISS] {konu} - Fetching from Google Trends...")
    start_time = time.time()
    
    pytrends = TrendReq(hl='tr-TR', tz=360, timeout=(10, 25))
    kw_list = [konu]
    
    # Payload oluştur
    pytrends.build_payload(kw_list, timeframe='today 12-m', geo='TR')
    
    def safe_request(func, *args, **kwargs):
        for _ in range(2):  # 2 retries
            try:
                sleep(0.5)
                return func(*args, **kwargs)
            except TooManyRequestsError:
                sleep(2)
            except Exception as e:
                print(f"Trends error: {e}")
                sleep(1)
        return None
    
    # Paralel olmayan ama sıralı istekler
    interest_over_time = safe_request(pytrends.interest_over_time)
    interest_by_region = safe_request(pytrends.interest_by_region)
    related_topics = safe_request(pytrends.related_topics)
    related_queries = safe_request(pytrends.related_queries)
    
    def safe_trending():
        try:
            return pytrends.trending_searches(pn='turkey')
        except Exception:
            return None
            
    trending_searches = safe_request(safe_trending)
    
    def to_dict_safe(df):
        if df is None or (hasattr(df, 'empty') and df.empty):
            return {}
        return df.to_dict()
    
    # Sadece gerekli veriyi çıkar - AI için optimize edilmiş
    iot_data = to_dict_safe(interest_over_time)
    ibr_data = to_dict_safe(interest_by_region)
    
    # İlgili sorguları ve konuları temizle - sadece top 10
    rq_clean = _clean_related_queries(related_queries)
    rt_clean = _clean_related_topics(related_topics)
    ts_clean = to_dict_safe(trending_searches)
    
    trends_time = time.time() - start_time
    
    result = {
        "interest_over_time": iot_data,
        "interest_by_region": ibr_data,
        "related_topics": rt_clean,
        "related_queries": rq_clean,
        "trending_searches": ts_clean,
        "_meta": {
            "fetch_time_seconds": round(trends_time, 2),
            "keyword": konu,
            "cached": False,
            "cache_age_seconds": 0
        }
    }
    
    # 2. Cache'e kaydet
    _set_cache(konu, result)
    
    return result

def _clean_related_queries(related_queries) -> dict:
    """Sadece top 10 rising ve top 10 top queries döndür."""
    if not related_queries or not isinstance(related_queries, dict):
        return {}
    
    result = {}
    for kw, data in related_queries.items():
        if not isinstance(data, dict):
            continue
        top = data.get('top')
        rising = data.get('rising')
        result[kw] = {
            "top": top.head(10).to_dict('records') if hasattr(top, 'head') else [],
            "rising": rising.head(10).to_dict('records') if hasattr(rising, 'head') else []
        }
    return result

def _clean_related_topics(related_topics) -> dict:
    """Sadece top 5 topic döndür."""
    if not related_topics or not isinstance(related_topics, dict):
        return {}
    
    result = {}
    for kw, data in related_topics.items():
        if not isinstance(data, dict):
            continue
        top = data.get('top')
        rising = data.get('rising')
        result[kw] = {
            "top": top.head(5).to_dict('records') if hasattr(top, 'head') else [],
            "rising": rising.head(5).to_dict('records') if hasattr(rising, 'head') else []
        }
    return result