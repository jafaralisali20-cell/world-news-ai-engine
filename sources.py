"""
sources.py - Global Source Registry for WorldNewsLi AI Engine
Covers: YouTube, Telegram, Satellite RSS, Agencies, Facebook Mirrors
"""

# ================================================================
# TELEGRAM CHANNELS (0-Latency WebSocket Engine)
# ================================================================
TG_CHANNELS = [
    # ── IRAQ ──────────────────────────────────────────────────
    "falafeliraqia",        # Iraqi news mirror
    "A_M_H1",              # Iraqi military news
    "centerkaf",           # Center Kaf political analysis
    "Alfaqaar313",         # Iraqi militia channel
    "almawqef_tv",         # Al Mawqef TV
    "knat_b2sonshadeed",   # B-2 Shadeed Iraqi
    "Alomhoar",            # Iraqi popular channel
    "SabrenNewss",         # Sabreen News
    "TANFITHY",            # Iraqi executive channel
    "mayadeenchannel",     # Mayadeen Iraq mirror
    "Iraq_now3",           # Iraq Now breaking
    "alsharqiyagroup",     # Al Sharqiya Group
    "iraqi1_news",         # Iraqi 1 News
    "Aletejahchanal",      # Al Etejah Iraq
    "iraqedu",             # Iraqi Education & News
    "imamhussain_ar",      # Imam Hussein Arabic
    "ina_news",            # Iraqi News Agency (INA)
    "Alforat_News",        # Al Forat News
    "baghdadtoday",        # Baghdad Today

    # ── IRAN ──────────────────────────────────────────────────
    "iraninarabic_ir",     # IRNA Arabic (Official)
    "tdofbdali313",        # Iran political news
    "iran_military_capabilities",  # Iran military channel
    "irnaarabi",           # IRNA Arabic Telegram
    "Tasnimnews_Ar",       # Tasnim News Arabic
    "Mehrnewsarabic",      # Mehr News Agency Arabic

    # ── ISRAEL / MILITARY ─────────────────────────────────────
    "AvichayAdraee",       # IDF Arabic Spokesman (Official)
    "idfarabic",           # IDF Arabic Channel

    # ── GLOBAL SATELLITES (Nilesat 2026) ──────────────────────
    "aljazeera",           # Al Jazeera Arabic  (12522 H)
    "alarabiya",           # Al Arabiya         (11747 V)
    "BBCArabic",           # BBC Arabic
    "RT_Arabic",           # RT Arabic          (11958 H)
    "SkyNewsArabia",       # Sky News Arabia    (11977 V)
    "cnnarabic",           # CNN Arabic
    "alhadath",            # Al Arabiya Al Hadath (11747 V)
    "alhurra",             # Al Hurra           (11258 H)
]

# ================================================================
# RSS FEEDS (Satellite + Agencies)
# ================================================================
RSS_FEEDS = {
    # ── Global Satellites ─────────────────────────────────────
    "Al Jazeera":        "https://www.aljazeera.net/aljazeerarss/a7c3d207-1647-498b-90e6-69d67a149c71/7a4239e3-861f-442a-9e8c-f05256e6d1fb",
    "Al Arabiya":        "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
    "Sky News Arabia":   "https://www.skynewsarabia.com/rss/feeds/rss.xml",
    "RT Arabic":         "https://arabic.rt.com/rss/",
    "BBC Arabic":        "https://feeds.bbci.co.uk/arabic/rss.xml",
    "CNN Arabic":        "https://arabic.cnn.com/rss/cnnarabic_world.rss",

    # ── Global Western Agencies ───────────────────────────────
    "Reuters Arabic":    "https://feeds.reuters.com/reuters/ar/topNews",

    # ── Iraq ──────────────────────────────────────────────────
    "INA Iraq":          "https://www.ina.iq/rss/",
    "Alsumaria":         "https://www.alsumaria.tv/rss",

    # ── Iran ──────────────────────────────────────────────────
    "Tasnim Arabic":     "https://www.tasnimnews.com/ar/rss/feed/0/7/0",

    # ── Israel ────────────────────────────────────────────────
    "Times of Israel":   "https://ar.timesofisrael.com/live-rss/",

    # ── USA / International ───────────────────────────────────
    "Al Hurra":          "https://www.alhurra.com/rss",
    "AP Arabic":         "https://apnews.com/rss",
}

# ================================================================
# YOUTUBE LIVE STREAMS (m3u8 + YouTube links)
# ================================================================
YOUTUBE_STREAMS = {
    "Al Jazeera Live":    "https://live-hls-web-aja.getaj.net/AJA/index.m3u8",
    "Al Arabiya Live":    "https://www.youtube.com/@alarabiya/live",
    "Sky News Live":      "https://www.youtube.com/@SkyNewsArabia/live",
    "RT Arabic Live":     "https://www.youtube.com/@RTarabic/live",
    "BBC Arabic Live":    "https://www.youtube.com/@bbcarabic/live",
    "Al Hurra Live":      "https://www.youtube.com/@AlHurraTV/live",
    "France 24 Arabic":   "https://www.youtube.com/@France24Arabic/live",
    "DW Arabic Live":     "https://www.youtube.com/@DWArabic/live",
}

# ================================================================
# SATELLITE METADATA (Nilesat 2026)
# ================================================================
SAT_DATA = {
    "Al Jazeera":     "📡 نايل سات: 12522 H (HD) | 10972 H (SD)",
    "Al Arabiya":     "📡 نايل سات: 11747 V",
    "Al Hadath":      "📡 نايل سات: 11747 V",
    "Sky News Arabia":"📡 نايل سات: 11977 V",
    "RT Arabic":      "📡 نايل سات: 11958 H",
    "Al Hurra":       "📡 نايل سات: 11258 H",
    "Al Iraqiya":     "📡 نايل سات: 12560 H",
    "BBC Arabic":     "📡 هوت بيرد: 10853 V",
    "France 24":      "📡 عرب سات: 12034 H",
}

# ================================================================
# SOURCE CATEGORIES (for n8n routing)
# ================================================================
SOURCE_CATEGORY = {
    "military":  ["iran_military_capabilities", "AvichayAdraee", "idfarabic", "A_M_H1"],
    "iraq":      ["INA Iraq", "Alsumaria", "baghdadtoday", "Alforat_News", "falafeliraqia"],
    "iran":      ["irnaarabi", "Tasnimnews_Ar", "Mehrnewsarabic", "Tasnim Arabic"],
    "israel":    ["Times of Israel", "AvichayAdraee"],
    "global":    ["Al Jazeera", "Al Arabiya", "Reuters Arabic", "BBC Arabic", "CNN Arabic"],
}
