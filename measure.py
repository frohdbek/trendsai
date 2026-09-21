import time
import os
from dotenv import load_dotenv

load_dotenv()
from app.services.trends_service import get_trend_data
from app.services.gemini_service import analyze_data

konu = "laptop"

# 1. Google Trends request + Data processing
t0 = time.time()
data = get_trend_data(konu)
t1 = time.time()

# 2. AI/Gemini request
t2 = time.time()
analysis = analyze_data(konu, data)
t3 = time.time()

print(f"Google Trends + Data processing time: {t1 - t0:.2f} s")
print(f"AI/Gemini request time: {t3 - t2:.2f} s")
print(f"Total time: {t3 - t0:.2f} s")
