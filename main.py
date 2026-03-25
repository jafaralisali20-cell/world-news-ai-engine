"""
WorldNewsLi - MASTER AI ENGINE
Full Multi-Source Integration (n8n + Claude 3.5 + Satellite + YouTube + Agencies)
Webhook: https://newstele.app.n8n.cloud/webhook/news-bot
"""
import os
import re
import hashlib
import io
import asyncio
from collections import deque
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import aiohttp
from aiohttp import web
from PIL import Image
import pytesseract
import feedparser
from motor.motor_asyncio import AsyncIOMotorClient
import anthropic

from sources import TG_CHANNELS, RSS_FEEDS, SAT_DATA, YOUTUBE_STREAMS
from n8n_client import push_to_n8n, push_sitrep_to_n8n

# ================================================================
# CONFIGURATION
# ================================================================
BOT_START_TIME   = datetime.now(timezone.utc)
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
TARGET_CHANNEL   = "@WorldNewsLi"
N8N_WEBHOOK      = "https://newstele.app.n8n.cloud/webhook/news-bot"
ANTHROPIC_KEY    = os.environ.get("ANTHROPIC_API_KEY",
    "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")

API_ID           = int(os.environ.get("TG_API_ID", "31030384"))
API_HASH         = os.environ.get("TG_API_HASH", "35b04ff5fb54744d4439f3d1c41e4230")
SESSION_STRING   = os.environ.get("SESSION_STRING", "")

ai_client        = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
print(f"[AI BOOT] WorldNewsLi Engine Online — {BOT_START_TIME.isoformat()}")

# ================================================================
# NEWS HISTORY (SitRep Analysis Buffer)
# ================================================================
news_history = deque(maxlen=50)

# ================================================================
# DATABASE & DEDUP
# ================================================================
MONGO_URI = os.environ.get("MONGO_URL") or os.environ.get("MONGO_URI", "")
db_client = AsyncIOMotorClient(MONGO_URI) if MONGO_URI else None
db_col    = db_client.news_bot.hashes if db_client else None
_seen     = set()

def make_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

async def is_processed(h: str) -> bool:
    if db_col: return bool(await db_col.find_one({"h": h}))
    return h in _seen

async def mark_processed(h: str):
    if db_col: await db_col.insert_one({"h": h})
    else:
        _seen.add(h)
        if len(_seen) > 8000: _seen.clear()

# ================================================================
# CLAUDE AI PIPELINE — Chief Satellite Military Editor
# ================================================================
SYSTEM_PROMPT = """
You are the Chief Satellite Military Editor of WorldNewsLi, with a SPECIAL STRATEGIC FOCUS on IRAQ (العراق).
Your ONLY job is to take ANY incoming Arabic/English news (even if informal, messy, or conversational) and strictly rephrase it into a highly formal, official broadcast news report. DO NOT ADD ANY EXTRA INFORMATION.

STRICT RULES:
1. 🔹 Start with a highly official, serious Arabic headline (max 12 words, bold).
2. ▪️ Follow with 1-3 tight factual bullet points using strictly formal news language (لغة إخبارية رسمية رصينة).
3. Remove ALL personal opinions, informal words, hashtags, URLs, t.me links, reporter names, and source signatures.
4. Replace all source mentions with "مَصادِرُنا".
5. Add footer: 📡 مَصادِرُنا | [SAT_INFO].
6. NEVER return an empty result unless the text is pure spam/ad — then return: EMPTY
7. Language: High-level formal Arabic ONLY (فصحى رسمية).
8. STRICT REPHRASING: You must completely transform unofficial text into an official statement.
"""

async def execute_ai_pipeline(
    raw_text: str,
    ocr_text: str = "",
    source_name: str = "",
) -> str:
    sat_info = SAT_DATA.get(source_name, "تغطية مستمرة")
    combined = (
        f"SOURCE: {source_name}\n"
        f"SAT: {sat_info}\n"
        f"NEWS: {raw_text}\n"
        f"OCR: {ocr_text}"
    )

    if not ai_client:
        clean = re.sub(r'https?://\S+|@\w+|#\w+|<[^>]+>', '', raw_text).strip()
        return f"🔹 {clean[:120]}\n\n▪️ تفاصيل إضافية\n📡 مَصادِرُنا | {sat_info}" if len(clean) > 30 else ""

    try:
        msg = await ai_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": combined}]
        )
        result = msg.content[0].text.strip()
        return "" if "EMPTY" in result[:10] else result
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return ""

# ================================================================
# STRATEGIC SITREP ANALYSIS
# ================================================================
SITREP_PROMPT = """
You are the Strategic Intelligence Analyst for WorldNewsLi.
Based on the recent news digest, produce a concise Strategic Situation Report (SitRep).

FORMAT:
🚩 [تحليل استراتيجي] (date + time context)
- 📈 التوجه العام: ...
- 🚨 مستوى التهديد: عالٍ / متوسط / منخفض
- 🎯 منطقة التركيز: ...
- ⚡ التطورات الميدانية: ...
- 📡 حالة الرصد: مُفعّل | جميع القنوات

RULES: Be concise. Arabic only. Strategic NOT tactical gossip.
"""

async def generate_sitrep() -> str | None:
    if not ai_client or len(news_history) < 5: return None
    combined = "\n---\n".join(list(news_history)[-30:])
    try:
        msg = await ai_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=800,
            system=SITREP_PROMPT,
            messages=[{"role": "user", "content": f"NEWS DIGEST:\n{combined}"}]
        )
        return msg.content[0].text.strip()
    except: return None

async def sitrep_loop(http: aiohttp.ClientSession):
    while True:
        await asyncio.sleep(600)  # every 10 min
        report = await generate_sitrep()
        if report:
            await push_sitrep_to_n8n(http, report)
            ok = await publish_to_telegram(http, report)
            print(f"[SITREP][{'OK' if ok else 'FAIL'}] Strategic Report Published.")

# ================================================================
# TELEGRAM PUBLISHING
# ================================================================
async def publish_to_telegram(http: aiohttp.ClientSession, text: str) -> bool:
    if not text: return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 تــابــعــنـا", "url": "https://t.me/WorldNewsLi"},
                {"text": "🔴 تواصل معنا", "url": "https://t.me/WorldNewsLi?direct"}
            ]
        ]
    }

    try:
        async with http.post(url, json={
            "chat_id": TARGET_CHANNEL,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": keyboard
        }, timeout=aiohttp.ClientTimeout(total=10)) as r:
            resp = await r.json()
            return resp.get("ok", False)
    except: return False

# ================================================================
# OCR — Image-to-Text
# ================================================================
async def extract_ocr(client: TelegramClient, msg) -> str:
    if msg.photo:
        try:
            buf = io.BytesIO()
            await client.download_media(msg.photo, file=buf)
            buf.seek(0)
            img = Image.open(buf)
            return pytesseract.image_to_string(img, lang="ara+eng")
        except: pass
    return ""

# ================================================================
# TELEGRAM EVENT HANDLER (0-Latency WebSocket)
# ================================================================
async def handle_telegram_event(
    event, client: TelegramClient, http: aiohttp.ClientSession
):
    msg = event.message
    if not msg.date or msg.date < BOT_START_TIME: return

    raw = msg.message or ""
    # Explicitly strip t.me and http links to prevent link injection
    raw = re.sub(r'https?://(?:www\.)?t\.me/[^\s]+', '', raw)
    raw = re.sub(r'https?://[^\s]+', '', raw)
    ocr = await extract_ocr(client, msg)
    combined = (raw + " " + ocr).strip()
    if len(combined) < 30: return

    # Dedup
    h = make_hash(combined[:400])
    if await is_processed(h): return
    await mark_processed(h)

    src = msg.chat.title if hasattr(msg.chat, "title") else "مَصادِرُنا"

    # AI
    post = await execute_ai_pipeline(raw, ocr, src)
    if not post: return

    # History
    news_history.append(post)

    # Dispatch
    await asyncio.gather(
        push_to_n8n(http, raw, post, src, "news", ocr),
        publish_to_telegram(http, post),
    )
    print(f"[TG][OK] {src}")

# ================================================================
# RSS ENGINE (5-Second Polling)
# ================================================================
_rss_initialized = False

async def poll_all_rss(http: aiohttp.ClientSession):
    global _rss_initialized
    for name, url in RSS_FEEDS.items():
        try:
            async with http.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status != 200: continue
                feed = feedparser.parse(await r.text())
        except: continue

        for entry in (feed.entries or [])[:7]:
            title = getattr(entry, "title", "")
            desc  = getattr(entry, "summary", "") or getattr(entry, "description", "")
            raw   = f"{title}. {desc}".strip()
            if len(raw) < 30: continue

            h = make_hash(raw[:400])
            if not _rss_initialized:
                await mark_processed(h)
                continue
            if await is_processed(h): continue
            await mark_processed(h)

            post = await execute_ai_pipeline(raw, source_name=name)
            if not post: continue

            news_history.append(post)
            await asyncio.gather(
                push_to_n8n(http, raw, post, name),
                publish_to_telegram(http, post),
            )
            print(f"[RSS][OK] {name}")

    if not _rss_initialized:
        print("[BOOT] RSS baseline cached. Live mode ON.")
        _rss_initialized = True

async def rss_loop(http: aiohttp.ClientSession):
    while True:
        await poll_all_rss(http)
        await asyncio.sleep(5)

# ================================================================
# HEALTH SERVER
# ================================================================
async def health(_):
    return web.Response(
                text="WorldNewsLi | Claude 3.5 + n8n + Nilesat | ACTIVE",
          content_type="text/plain"
)

# ================================================================
# MAIN ENTRYPOINT
# ================================================================
async def main():
    # Telegram connection
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("[FATAL] Telegram session invalid. Set SESSION_STRING variable.")
        return

    http = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=200))

    # Resolve channels via dynamic universal filtering (fixes muted/unopened channel issues)
    print("[INIT] Optimizing target channel cache for muted/live channels...")
    target_usernames = {ch.lower() for ch in TG_CHANNELS}

        @client.on(events.NewMessage())
        async def on_event(event):
                  chat = await event.get_chat()
                  username = getattr(chat, 'username', '')
                  if username and username.lower() in target_usernames:
                                await handle_telegram_event(event, client, http)

          # Health server
              app = web.Application()
        app.router.add_get("/", health)
        runner = web.AppRunner(app)
            await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()

        print("[PIPELINE] CLAUDE 3.5 + n8n + NILESAT ENGINE FULLY ONLINE")
        await asyncio.gather(
              client.run_until_disconnected(),
              rss_loop(http),
              sitrep_loop(http),
    )

if __name__ == "__main__":
    asyncio.run(main())
