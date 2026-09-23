from app.services.trends_service import get_trend_data
from app.services.groq_service import analyze_data
import os
from dotenv import load_dotenv

load_dotenv()

try:
    konu = "python"
    print("Fetching trend data...")
    data = get_trend_data(konu)
    print("Data fetched successfully.")
    print("Analyzing data...")
    analysis = analyze_data(konu, data)
    print("Analysis:")
    print(analysis)
except Exception as e:
    import traceback
    traceback.print_exc()
