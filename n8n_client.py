"""
n8n_client.py - WorldNewsLi n8n Cloud Integration
Webhook: https://newstele.app.n8n.cloud/webhook/news-bot
"""
import aiohttp
import json
from datetime import datetime, timezone
from sources import SOURCE_CATEGORY, SAT_DATA

N8N_WEBHOOK = "https://newstele.app.n8n.cloud/webhook/news-bot"

# ================================================================
# PAYLOAD BUILDER
# ================================================================
def build_payload(
    raw: str,
    ai_post: str,
    source_name: str,
    post_type: str = "news",  # "news" | "sitrep" | "ocr"
    ocr_text: str = "",
) -> dict:
    """Build a rich, structured JSON payload for n8n automation."""
    
    # Determine category
    category = "general"
    for cat, sources in SOURCE_CATEGORY.items():
        if source_name in sources:
            category = cat
            break

    # Determine urgency from keywords
    urgency_keywords = ["عاجل", "عاجلة", "صاروخ", "غارة", "انفجار", "هجوم", "اشتباك"]
    is_urgent = any(kw in (raw + ai_post) for kw in urgency_keywords)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source_name,
        "category": category,
        "type": post_type,
        "urgency": "HIGH" if is_urgent else "NORMAL",
        "sat_data": SAT_DATA.get(source_name, "تغطية مستمرة"),
        "raw": raw[:1000],         # original text (truncated)
        "ai_post": ai_post,        # Claude-processed post
        "ocr": ocr_text[:500],     # OCR data if available
        "channel": "@WorldNewsLi",
    }

# ================================================================
# N8N HTTP CLIENT WITH RETRY
# ================================================================
async def push_to_n8n(
    http: aiohttp.ClientSession,
    raw: str,
    ai_post: str,
    source_name: str = "",
    post_type: str = "news",
    ocr_text: str = "",
    retries: int = 3,
):
    """Send a structured payload to the n8n webhook with auto-retry."""
    payload = build_payload(raw, ai_post, source_name, post_type, ocr_text)
    
    for attempt in range(retries):
        try:
            async with http.post(
                N8N_WEBHOOK,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=8),
                headers={"Content-Type": "application/json"}
            ) as r:
                if r.status < 400:
                    print(f"[N8N][OK] → {source_name} | Type: {post_type} | Urgency: {payload['urgency']}")
                    return
                else:
                    print(f"[N8N][ERR {r.status}] Attempt {attempt+1}/{retries}")
        except Exception as e:
            print(f"[N8N][FAIL] Attempt {attempt+1}/{retries}: {e}")

async def push_sitrep_to_n8n(http: aiohttp.ClientSession, report_text: str):
    """Specific function for sending Strategic SitRep to n8n."""
    await push_to_n8n(http, "", report_text, "WorldNewsLi Strategic", "sitrep")
