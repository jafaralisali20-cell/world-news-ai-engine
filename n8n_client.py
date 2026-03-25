"""
n8n_client.py
"""
import aiohttp
import json
from datetime import datetime, timezone
from sources import SOURCE_CATEGORY, SAT_DATA

N8N_WEBHOOK = "https://newstele.app.n8n.cloud/webhook/news-bot"

def build_payload(raw, ai_post, source_name, post_type="news", ocr_text=""):
      category = "general"
      for cat, sources in SOURCE_CATEGORY.items():
                if source_name in sources:
                              category = cat
                              break
                      is_urgent = False
            return {
                      "timestamp": datetime.now(timezone.utc).isoformat(),
                      "source": source_name,
                      "category": category,
                      "type": post_type,
                      "urgency": "NORMAL",
                      "sat_data": "Continuous Coverage",
                      "raw": raw[:1000],
                      "ai_post": ai_post,
                      "ocr": ocr_text[:500],
                      "channel": "@WorldNewsLi",
            }
async def push_to_n8n(http, raw, ai_post, source_name="", post_type="news", ocr_text="", retries=3):
      payload = build_payload(raw, ai_post, source_name, post_type, ocr_text)
    for attempt in range(retries):
              try:
                            async with http.post(N8N_WEBHOOK, json=payload, timeout=8) as r:
                                              if r.status < 400: return
                                                        except: pass

      async def push_sitrep_to_n8n(http, report_text):
            await push_to_n8n(http, "", report_text, "WorldNewsLi Strategic", "sitrep")
