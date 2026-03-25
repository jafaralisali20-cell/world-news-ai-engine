f"""
WorldNewsLi - AI ENGINE (Claude 3.5 + n8n + ZERO LATENCY)
The ultimate 24/7 autonomous news agency.
Features: 
- Anthropic Claude 3.5 Sonnet for Radical Summarization.
- n8n Machine Connectivity for automated distribution.
- Telethon 0-Latency WebSockets for instant scraping.
- Pure Text + OCR image-to-text conversion.
"""
import os
import re
import hashlib
import io
import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from time import mktime

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import aiohttp
from aiohttp import web
from PIL import Image
import pytesseract
import feedparser
from motor.motor_asyncio import AsyncIOMotorClient
import anthropic

# ================================================================
# CONFIGURATION & ENVIRONMENT
# ================================================================
BOT_START_TIME = datetime.now(timezone.utc)
print(f"[AI BOOT] Engine initialized at: {BOT_START_TIME}")

# Core Tokens
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
TARGET_CHANNEL   = "@WorldNewsLi"
ANTHROPIC_KEY    = os.environ.get("ANTHROPIC_API_KEY", "")
N8N_WEBHOOK      = os.environ.get("N8N_WEBHOOK_URL", "")

# Telethon Config
API_ID           = int(os.environ.get("TG_API_ID", "31030384"))
API_HASH         = os.environ.get("TG_API_HASH", "35b04ff5fb54744d4439f3d1c41e4230")
SESSION_STRING   = os.environ.get("SESSION_STRING", "")

# AI Client
ai_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

# ================================================================
# SOURCES
# ================================================================
TG_CHANNELS = [
      "falafeliraqia", "A_M_H1", "centerkaf", "Alfaqaar313", "almawqef_tv",
      "knat_b2sonshadeed", "Alomhoar", "SabrenNewss", "TANFITHY", "mayadeenchannel",
      "Iraq_now3", "alsharqiyagroup", "Educationiq", "iraqi1_news", "Aletejahchanal",
      "iraninarabic_ir", "tdofbdali313", "iran_military_capabilities", "iraqedu", "imamhussain_ar",
      "aljazeera", "alarabiya", "BBCArabic", "RT_Arabic", "SkyNewsArabia", "cnnarabic", "alhadath"
]

RSS_FEEDS = {
      "Al Jazeera": "https://www.aljazeera.net/aljazeerarss/a7c3d207-1647-498b-90e6-69d67a149c71/7a4239e3-861f-442a-9e8c-f05256e6d1fb",
      "Al Arabiya": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
      "Sky News": "https://www.skynewsarabia.com/rss/feeds/rss.xml",
      "RT Arabic": "https://arabic.rt.com/rss/",
      "Reuters": "https://feeds.reuters.com/reuters/ar/topNews",
      "BBC Arabic": "https://feeds.bbci.co.uk/arabic/rss.xml",
      "CNN Arabic": "https://arabic.cnn.com/rss/cnnarabic_world.rss"
}

# ================================================================
# CACHING & DEDUPLICATION
# ================================================================
MONGO_URI     = os.environ.get("MONGO_URL") or os.environ.get("MONGO_URI", "")
db_client     = AsyncIOMotorClient(MONGO_URI) if MONGO_URI else None
db_col        = db_client.news_bot.hashes if db_client else None
_seen         = set()
recent        = deque(maxlen=1000)

def make_hash(text: str) -> str:
      return hashlib.md5(text.encode()).hexdigest()

async def is_processed(h: str) -> bool:
      if db_col: return bool(await db_col.find_one({"h": h}))
            return h in _seen

async def mark_processed(h: str):
      if db_col: await db_col.insert_one({"h": h})
else:
        _seen.add(h)
          if len(_seen) > 5000: _seen.clear()

# ================================================================
# CLAUDE AI ENGINE (The Neural 10-Tool Pipeline)
# ================================================================
SYSTEM_PROMPT = """
You are the Chief Editor of WorldNewsLi Arabic Agency. 
Your goal is to rephrase and summarize incoming news into a radical, professional, and ultra-short format.

RULES:
1. NORMALIZE: Ensure proper Arabic script.
2. CLEAN: Remove ALL hashtags, URLs, HTML tags, and @mentions.
3. ANTI-BRAND: Remove source names (Al Jazeera, RT, etc.) and replace with "OUR_SOURCES".
4. SUMMARIZE: Provide a single bold headline and 2 max 3 bullet points for key details.
5. NO EMPTY: If the input is junk, return EMPTY.
6. NO EMOJIS: Use only punctuation and bullet points (*, >).
7. TONE: Serious, informative, professional broadcast style.
8. OUTPUT: ONLY the summarized text in Arabic. No explanations.
"""

async def execute_ai_pipeline(raw_text: str, ocr_text: str = "") -> str:
      combined = f"INPUT NEWS: {raw_text}\nOCR TEXT: {ocr_text}"
    if not ai_client:
              # Fallback to simple cleaning if Claude is offline
              clean = re.sub(r'https?://\S+|@\w+|#\w+|<[^>]+>', '', combined).strip()
              return f"> {clean[:100]}...\n\n* Additional details in the channel."

    try:
              msg = await ai_client.messages.create(
                            model="claude-3-5-sonnet-20240620",
                            max_tokens=500,
                            system=SYSTEM_PROMPT,
                            messages=[{"role": "user", "content": combined}]
              )
              return msg.content[0].text
except Exception as e:
        print(f"[AI ERROR] {e}")
        return ""

# ================================================================
# N8N MACHINE CONNECTIVITY
# ================================================================
async def push_to_n8n(http: aiohttp.ClientSession, payload: dict):
      if not N8N_WEBHOOK: return
            try:
                      async with http.post(N8N_WEBHOOK, json=payload, timeout=5) as r:
                                    pass
                            except: pass

# ================================================================
# CORE LOGIC & MEDIA
# ================================================================
async def extract_ocr(client: TelegramClient, msg) -> str:
      if msg.photo:
                try:
                              buf = io.BytesIO()
                              await client.download_media(msg.photo, file=buf)
                              buf.seek(0)
                              img = Image.open(buf)
                              return pytesseract.image_to_string(img, lang="ara")
                          except: pass
    return ""

async def publish_telegram(http: aiohttp.ClientSession, text: str):
      if not text or "EMPTY" in text: return False
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with http.post(url, json={
              "chat_id": TARGET_CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True
    }, timeout=10) as r:
              resp = await r.json()
        return resp.get("ok", False)

async def handle_telegram_event(event, client: TelegramClient, http: aiohttp.ClientSession):
      msg = event.message
    if not msg.date or msg.date < BOT_START_TIME: return

    raw = msg.message or ""
    ocr = await extract_ocr(client, msg)
    combined = (raw + " " + ocr).strip()
    if len(combined) < 30: return

    # Deduplication
    h = make_hash(combined[:400])
    if await is_processed(h): return
          await mark_processed(h)

    # AI Processing
    final_post = await execute_ai_pipeline(raw, ocr)
    if not final_post: return

    # Push to n8n (Optional Orchestration)
    await push_to_n8n(http, {"source": "Telegram", "raw": raw, "ai_post": final_post, "ocr": ocr})

    # Final Post
    ok = await publish_telegram(http, final_post)
    print(f"[AI ENGINE][{'OK' if ok else 'FAIL'}] Event from Telegram Stream.")

# ================================================================
# RSS POLLING ENGINE
# ================================================================
RSS_INITIALIZED = False

async def poll_rss(http: aiohttp.ClientSession):
      global RSS_INITIALIZED
    for name, url in RSS_FEEDS.items():
              try:
                            async with http.get(url, timeout=5) as r:
                                              if r.status != 200: continue
                                                                feed = feedparser.parse(await r.text())
                                      except: continue

        for entry in feed.entries[:5]:
                      raw = f"{getattr(entry, 'title','')}. {getattr(entry, 'description','')}"
            if len(raw) < 30: continue

            h = make_hash(raw[:400])
            if not RSS_INITIALIZED:
                              await mark_processed(h)
                              continue

            if await is_processed(h): continue
                          await mark_processed(h)

            # AI Processing
            final_post = await execute_ai_pipeline(raw)
            if not final_post: continue

            # Push to n8n
            await push_to_n8n(http, {"source": "RSS", "provider": name, "raw": raw, "ai_post": final_post})

            ok = await publish_telegram(http, final_post)
            print(f"[AI ENGINE][{'OK' if ok else 'FAIL'}] {name} (RSS)")

    if not RSS_INITIALIZED:
              print("[BOOT] Base RSS mapping completed.")
        RSS_INITIALIZED = True

async def poll_rss_loop(http: aiohttp.ClientSession):
      while True:
                await poll_rss(http)
        await asyncio.sleep(5)

# ================================================================
# MASTER SERVER
# ================================================================
async def health(_): return web.Response(text="WorldNewsLi AI Engine (Claude 3.5 + n8n) is Active.")

async def main():
      client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized(): 
              print("[FATAL] Sesion check failed.")
        return

    http = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=100))

    valid_chats = []
    print("[INIT] Connecting AI Scraper to 0-Latency Sockets...")
    for ch in TG_CHANNELS:
              try: valid_chats.append(await client.get_entity(ch))
                        except: print(f"[INIT SKIP] {ch}")

    @client.on(events.NewMessage(chats=valid_chats))
    async def on_new(event): await handle_telegram_event(event, client, http)

    app = web.Application()
    app.router.add_get("/", health)
    r = web.AppRunner(app)
    await r.setup()
    await web.TCPSite(r, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()

    print(f"[PIPELINE] CLAUDE 3.5 AI ENGINE ONLINE.")
    await asyncio.gather(client.run_until_disconnected(), poll_rss_loop(http))

if __name__ == "__main__":
      asyncio.run(main())
