#!/usr/bin/env python3
"""Telegram OTP Number Bot v2 - Optimized for Termux"""

import os, json, asyncio, logging, time, re
from pathlib import Path

import aiohttp
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from telegram.constants import ParseMode, ChatMemberStatus

# ── Config ──────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8712078921:AAEyaI9wfab8-iOcd-TFfqvN3h-bagalfpo")
API_KEY = os.environ.get("API_KEY", "nxa_1a440d9fd9df7c320e4f61f8b221fe8663ffdd40")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6668016879"))
API_BASE = "http://185.190.142.81/api/v1"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

DATA_DIR = Path(__file__).parent
USERS_FILE = DATA_DIR / "users.json"
CONFIG_FILE = DATA_DIR / "config.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
log = logging.getLogger("bot")

# ── Country Flags ───────────────────────────────────
COUNTRY_FLAGS = {
    "afghanistan": "🇦🇫", "albania": "🇦🇱", "algeria": "🇩🇿", "andorra": "🇦🇩",
    "angola": "🇦🇴", "argentina": "🇦🇷", "armenia": "🇦🇲", "australia": "🇦🇺",
    "austria": "🇦🇹", "azerbaijan": "🇦🇿", "bahamas": "🇧🇸", "bahrain": "🇧🇭",
    "bangladesh": "🇧🇩", "barbados": "🇧🇧", "belarus": "🇧🇾", "belgium": "🇧🇪",
    "belize": "🇧🇿", "benin": "🇧🇯", "bhutan": "🇧🇹", "bolivia": "🇧🇴",
    "bosnia": "🇧🇦", "botswana": "🇧🇼", "brazil": "🇧🇷", "brunei": "🇧🇳",
    "bulgaria": "🇧🇬", "burkina faso": "🇧🇫", "burundi": "🇧🇮", "cambodia": "🇰🇭",
    "cameroon": "🇨🇲", "canada": "🇨🇦", "chile": "🇨🇱", "china": "🇨🇳",
    "colombia": "🇨🇴", "congo": "🇨🇬", "costa rica": "🇨🇷", "croatia": "🇭🇷",
    "cuba": "🇨🇺", "cyprus": "🇨🇾", "czech republic": "🇨🇿", "denmark": "🇩🇰",
    "djibouti": "🇩🇯", "dominican republic": "🇩🇴", "ecuador": "🇪🇨", "egypt": "🇪🇬",
    "el salvador": "🇸🇻", "estonia": "🇪🇪", "ethiopia": "🇪🇹", "fiji": "🇫🇯",
    "finland": "🇫🇮", "france": "🇫🇷", "gabon": "🇬🇦", "gambia": "🇬🇲",
    "georgia": "🇬🇪", "germany": "🇩🇪", "ghana": "🇬🇭", "greece": "🇬🇷",
    "guatemala": "🇬🇹", "guinea": "🇬🇳", "haiti": "🇭🇹", "honduras": "🇭🇳",
    "hungary": "🇭🇺", "iceland": "🇮🇸", "india": "🇮🇳", "indonesia": "🇮🇩",
    "iran": "🇮🇷", "iraq": "🇮🇶", "ireland": "🇮🇪", "israel": "🇮🇱",
    "italy": "🇮🇹", "jamaica": "🇯🇲", "japan": "🇯🇵", "jordan": "🇯🇴",
    "kazakhstan": "🇰🇿", "kenya": "🇰🇪", "kuwait": "🇰🇼", "kyrgyzstan": "🇰🇬",
    "laos": "🇱🇦", "latvia": "🇱🇻", "lebanon": "🇱🇧", "libya": "🇱🇾",
    "lithuania": "🇱🇹", "luxembourg": "🇱🇺", "madagascar": "🇲🇬", "malawi": "🇲🇼",
    "malaysia": "🇲🇾", "maldives": "🇲🇻", "mali": "🇲🇱", "malta": "🇲🇹",
    "mauritius": "🇲🇺", "mexico": "🇲🇽", "moldova": "🇲🇩", "mongolia": "🇲🇳",
    "morocco": "🇲🇦", "mozambique": "🇲🇿", "myanmar": "🇲🇲", "namibia": "🇳🇦",
    "nepal": "🇳🇵", "netherlands": "🇳🇱", "new zealand": "🇳🇿", "nicaragua": "🇳🇮",
    "niger": "🇳🇪", "nigeria": "🇳🇬", "norway": "🇳🇴", "oman": "🇴🇲",
    "pakistan": "🇵🇰", "palestine": "🇵🇸", "panama": "🇵🇦", "paraguay": "🇵🇾",
    "peru": "🇵🇪", "philippines": "🇵🇭", "poland": "🇵🇱", "portugal": "🇵🇹",
    "qatar": "🇶🇦", "romania": "🇷🇴", "russia": "🇷🇺", "rwanda": "🇷🇼",
    "saudi arabia": "🇸🇦", "senegal": "🇸🇳", "serbia": "🇷🇸", "singapore": "🇸🇬",
    "slovakia": "🇸🇰", "slovenia": "🇸🇮", "somalia": "🇸🇴", "south africa": "🇿🇦",
    "south korea": "🇰🇷", "spain": "🇪🇸", "sri lanka": "🇱🇰", "sudan": "🇸🇩",
    "sweden": "🇸🇪", "switzerland": "🇨🇭", "syria": "🇸🇾", "taiwan": "🇹🇼",
    "tajikistan": "🇹🇯", "tanzania": "🇹🇿", "thailand": "🇹🇭", "togo": "🇹🇬",
    "tunisia": "🇹🇳", "turkey": "🇹🇷", "uganda": "🇺🇬", "ukraine": "🇺🇦",
    "united arab emirates": "🇦🇪", "united kingdom": "🇬🇧", "united states": "🇺🇸",
    "uruguay": "🇺🇾", "uzbekistan": "🇺🇿", "venezuela": "🇻🇪", "vietnam": "🇻🇳",
    "yemen": "🇾🇪", "zambia": "🇿🇲", "zimbabwe": "🇿🇼",
    "usa": "🇺🇸", "uk": "🇬🇧", "uae": "🇦🇪", "hong kong": "🇭🇰",
}

# ── Phone Code → Country (auto-detection) ──────────
PHONE_CODES = {
    "1": "united states", "7": "russia", "20": "egypt", "27": "south africa",
    "30": "greece", "31": "netherlands", "32": "belgium", "33": "france",
    "34": "spain", "36": "hungary", "39": "italy", "40": "romania",
    "41": "switzerland", "43": "austria", "44": "united kingdom", "45": "denmark",
    "46": "sweden", "47": "norway", "48": "poland", "49": "germany",
    "51": "peru", "52": "mexico", "53": "cuba", "54": "argentina",
    "55": "brazil", "56": "chile", "57": "colombia", "58": "venezuela",
    "60": "malaysia", "61": "australia", "62": "indonesia", "63": "philippines",
    "64": "new zealand", "65": "singapore", "66": "thailand", "81": "japan",
    "82": "south korea", "84": "vietnam", "86": "china", "90": "turkey",
    "91": "india", "92": "pakistan", "93": "afghanistan", "94": "sri lanka",
    "95": "myanmar", "98": "iran", "212": "morocco", "213": "algeria",
    "216": "tunisia", "218": "libya", "220": "gambia", "221": "senegal",
    "223": "mali", "224": "guinea", "226": "burkina faso", "227": "niger",
    "228": "togo", "229": "benin", "230": "mauritius", "231": "liberia",
    "233": "ghana", "234": "nigeria", "235": "chad", "237": "cameroon",
    "240": "equatorial guinea", "241": "gabon", "242": "congo",
    "244": "angola", "248": "seychelles", "249": "sudan", "250": "rwanda",
    "251": "ethiopia", "252": "somalia", "253": "djibouti", "254": "kenya",
    "255": "tanzania", "256": "uganda", "257": "burundi", "258": "mozambique",
    "260": "zambia", "261": "madagascar", "263": "zimbabwe", "264": "namibia",
    "265": "malawi", "266": "lesotho", "267": "botswana", "269": "comoros",
    "291": "eritrea", "350": "gibraltar", "351": "portugal", "352": "luxembourg",
    "353": "ireland", "354": "iceland", "355": "albania", "356": "malta",
    "357": "cyprus", "358": "finland", "359": "bulgaria", "370": "lithuania",
    "371": "latvia", "372": "estonia", "373": "moldova", "374": "armenia",
    "375": "belarus", "380": "ukraine", "381": "serbia", "385": "croatia",
    "386": "slovenia", "387": "bosnia", "420": "czech republic", "421": "slovakia",
    "880": "bangladesh", "886": "taiwan", "960": "maldives", "961": "lebanon",
    "962": "jordan", "963": "syria", "964": "iraq", "965": "kuwait",
    "966": "saudi arabia", "967": "yemen", "968": "oman", "970": "palestine",
    "971": "united arab emirates", "972": "israel", "973": "bahrain",
    "974": "qatar", "975": "bhutan", "976": "mongolia", "977": "nepal",
    "992": "tajikistan", "993": "turkmenistan", "994": "azerbaijan",
    "995": "georgia", "996": "kyrgyzstan", "998": "uzbekistan",
}

SERVICE_SHORTS = {
    "facebook": "FB", "whatsapp": "WA", "whatsapp businesses": "WB",
    "telegram": "TG", "instagram": "IG", "twitter": "TW", "x": "X",
    "google": "GO", "gmail": "GM", "youtube": "YT", "apple": "AP",
    "microsoft": "MS", "tiktok": "TT", "snapchat": "SC", "binance": "BN",
    "melbet": "MB", "bkash": "BK", "rocket": "RK", "nagad": "NG",
    "imo": "IMO", "messenger": "MS", "custom search": "CS",
}

EMOJI = {
    "done": "✅", "cross": "❌", "warn": "⚠️", "time": "⏰",
    "wait": "🔄", "otp": "🔐", "number": "📞", "user": "👤",
    "globe": "🌍", "star": "⭐", "crown": "👑", "fire": "🔥",
    "key": "🔑", "lock": "🔒", "bell": "🔔", "rocket": "🚀",
    "lightning": "⚡", "gear": "⚙️", "mega": "📢", "pin": "📌",
}

# ── Storage ─────────────────────────────────────────
def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def get_config():
    default = {
        "channels": ["@channel1", "@channel2"],
        "ranges": {"Tajikistan": {"code": "+992", "range": "99298XXX", "flag": "🇹🇯"}},
    }
    cfg = _load(CONFIG_FILE, default)
    _save(CONFIG_FILE, cfg)
    return cfg

def get_users():
    return _load(USERS_FILE, {})

def save_user(uid, data):
    u = get_users()
    u[str(uid)] = data
    _save(USERS_FILE, u)

def get_sessions():
    return _load(SESSIONS_FILE, {})

def save_session(uid, sess):
    s = get_sessions()
    s[str(uid)] = sess
    _save(SESSIONS_FILE, s)

def del_session(uid):
    s = get_sessions()
    s.pop(str(uid), None)
    _save(SESSIONS_FILE, s)

# ── Helpers ─────────────────────────────────────────
def flag_for(country):
    return COUNTRY_FLAGS.get(country.lower(), "🏳️")

def detect_country(range_str: str):
    digits = re.sub(r"[^0-9]", "", range_str)
    for length in (3, 2, 1):
        code = digits[:length]
        if code in PHONE_CODES:
            name = PHONE_CODES[code]
            return name.title(), f"+{code}", COUNTRY_FLAGS.get(name, "🏳️")
    return "Unknown", "", "🏳️"

# ── Concurrency guards ──────────────────────────────
_polls: dict[int, asyncio.Task] = {}
_locks: dict[int, asyncio.Lock] = {}
_rl: dict[int, float] = {}
_msg_track: dict[int, int] = {}
_support_wait: set[int] = set()
_bcast_wait: set[int] = set()
RATE_SEC = 3

def _lock(uid: int) -> asyncio.Lock:
    if uid not in _locks:
        _locks[uid] = asyncio.Lock()
    return _locks[uid]

def _rate_ok(uid: int) -> bool:
    now = time.time()
    if now - _rl.get(uid, 0) < RATE_SEC:
        return False
    _rl[uid] = now
    return True

# ── Shared HTTP session ─────────────────────────────
_http: aiohttp.ClientSession | None = None

async def get_http() -> aiohttp.ClientSession:
    global _http
    if _http is None or _http.closed:
        _http = aiohttp.ClientSession(
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=15),
        )
    return _http

async def close_http():
    global _http
    if _http and not _http.closed:
        await _http.close()
        _http = None

# ── API Client (with retry) ────────────────────────
async def api_get_number(range_str: str, retries=2) -> dict | None:
    body = {"range": range_str, "format": "national"}
    s = await get_http()
    for attempt in range(retries + 1):
        try:
            async with s.post(f"{API_BASE}/numbers/get", json=body) as r:
                if r.status == 200:
                    return await r.json()
                log.warning("get_number %s: %s", r.status, await r.text())
        except Exception as e:
            log.warning("get_number err(%d): %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(1)
    return None

async def api_get_sms(number_id: str, retries=2) -> dict | None:
    s = await get_http()
    for attempt in range(retries + 1):
        try:
            async with s.get(f"{API_BASE}/numbers/{number_id}/sms") as r:
                if r.status == 200:
                    return await r.json()
        except Exception as e:
            log.warning("get_sms err(%d): %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(1)
    return None

async def api_logs(limit=50) -> dict | None:
    s = await get_http()
    try:
        async with s.get(f"{API_BASE}/console/logs", params={"limit": limit}) as r:
            if r.status == 200:
                return await r.json()
    except Exception as e:
        log.warning("logs err: %s", e)
    return None

# ── Channel check ───────────────────────────────────
async def check_joined(ctx: ContextTypes.DEFAULT_TYPE, uid: int):
    cfg = get_config()
    missing = []
    for ch in cfg.get("channels", []):
        try:
            m = await ctx.bot.get_chat_member(ch, uid)
            if m.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return len(missing) == 0, missing

# ── Admin notify (upgraded) ─────────────────────────
async def notify_admin(ctx, user, number="", otp="", country=""):
    name = getattr(user, "full_name", "Unknown")
    uname = f"@{user.username}" if getattr(user, "username", None) else "N/A"
    lines = [f"👤 {name}", f"{uname} | <code>{user.id}</code>", ""]
    if country:
        lines.append(f"🌍 {country}")
    if number:
        lines.append(f"📱 Number - <code>{number}</code>")
    if otp:
        lines.append(f"🔑 OTP - <code>{otp}</code>")
    try:
        await ctx.bot.send_message(ADMIN_ID, "\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("notify err: %s", e)

# ── Smart OTP parser ────────────────────────────────
def extract_otp(data: dict) -> str:
    for key in ("otp", "code", "sms"):
        val = data.get(key)
        if val:
            return str(val)
    text = data.get("text", "")
    if text:
        m = re.search(r"\b(\d{4,8})\b", text)
        if m:
            return m.group(1)
    return ""

# ── OTP polling (with message delete) ───────────────
async def poll_otp(ctx, uid: int, user, number_id: str, number: str, country: str):
    try:
        for _ in range(600):
            data = await api_get_sms(number_id)
            if data:
                status = data.get("status", "")
                if status == "success":
                    otp = extract_otp(data)
                    if uid in _msg_track:
                        try:
                            await ctx.bot.delete_message(uid, _msg_track[uid])
                        except Exception:
                            pass
                        _msg_track.pop(uid, None)
                    text = (
                        f"Number - <code>{number}</code>\n"
                        f"OTP - <code>{otp}</code>"
                    )
                    try:
                        await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML)
                    except Exception:
                        pass
                    await notify_admin(ctx, user, number, str(otp), country)
                    del_session(uid)
                    _polls.pop(uid, None)
                    return
                elif status != "pending":
                    break
            await asyncio.sleep(2)
        try:
            await ctx.bot.send_message(uid, "⏰ OTP timed out. Try a new number.")
        except Exception:
            pass
    finally:
        del_session(uid)
        _polls.pop(uid, None)
        _msg_track.pop(uid, None)

# ── Main keyboard ───────────────────────────────────
MAIN_KB = ReplyKeyboardMarkup(
    [["📲 Get Number"], ["📊 View Ranges", "📞 Contact Admin"], ["💬 Support"]],
    resize_keyboard=True,
)

# ── /start ──────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, {"name": user.full_name, "username": user.username, "ts": time.time()})
    ok, missing = await check_joined(ctx, user.id)
    if not ok:
        btns = [
            [InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}")]
            for ch in missing
        ]
        btns.append([InlineKeyboardButton("✅ Check", callback_data="check_join")])
        await update.message.reply_text(
            "Please join these channels first:",
            reply_markup=InlineKeyboardMarkup(btns),
        )
        return
    await update.message.reply_text("Welcome! Tap below to get started.", reply_markup=MAIN_KB)

async def cb_check_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ok, _ = await check_joined(ctx, q.from_user.id)
    if not ok:
        await q.answer("You haven't joined all channels yet.", show_alert=True)
        return
    await q.message.reply_text("Welcome! Tap below to get started.", reply_markup=MAIN_KB)

# ── Get number (with animation) ────────────────────
async def _do_get_number(ctx, user, chat_id, range_str=None, country=None):
    if user.id in _polls:
        _polls[user.id].cancel()
        _polls.pop(user.id, None)

    cfg = get_config()
    ranges = cfg.get("ranges", {})
    if not ranges:
        await ctx.bot.send_message(chat_id, "No ranges configured. Contact admin.")
        return

    if not range_str:
        country = list(ranges.keys())[0]
        range_str = ranges[country]["range"]

    if not country or country == "Unknown":
        country, _, _ = detect_country(range_str)

    loading = await ctx.bot.send_message(chat_id, "⏳ Getting number...")

    async with _lock(user.id):
        data = await api_get_number(range_str)

    if not data or "number" not in data:
        await loading.edit_text("❌ Failed to get number. Try again.")
        return

    number = data["number"]
    nid = data["number_id"]
    save_session(user.id, {
        "number_id": nid, "number": number,
        "range": range_str, "country": country, "ts": time.time(),
    })

    auto_save_range(range_str, country)

    text = f"Number - <code>{number}</code>"
    btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Same Range", callback_data=f"same_{range_str}")]]
    )
    msg = await loading.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=btn)
    _msg_track[user.id] = msg.message_id

    await notify_admin(ctx, user, number, country=country)
    task = asyncio.create_task(poll_otp(ctx, user.id, user, nid, number, country))
    _polls[user.id] = task

def auto_save_range(range_str: str, country: str):
    cfg = get_config()
    for info in cfg.get("ranges", {}).values():
        if info.get("range") == range_str:
            return
    name, code, flag = detect_country(range_str)
    if country and country != "Unknown":
        name = country
        flag = COUNTRY_FLAGS.get(country.lower(), flag)
    cfg.setdefault("ranges", {})[name] = {"code": code, "range": range_str, "flag": flag}
    _save(CONFIG_FILE, cfg)

async def handle_get_number(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ok, _ = await check_joined(ctx, user.id)
    if not ok:
        await update.message.reply_text("Please /start and join channels first.")
        return
    if not _rate_ok(user.id):
        await update.message.reply_text("Please wait a moment...")
        return
    await _do_get_number(ctx, user, update.effective_chat.id)

async def cb_same_range(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    if not _rate_ok(user.id):
        await q.answer("Please wait...", show_alert=True)
        return
    range_str = q.data.removeprefix("same_")
    sess = get_sessions().get(str(user.id), {})
    country = sess.get("country")
    await _do_get_number(ctx, user, q.message.chat_id, range_str, country)

async def cb_use_range(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    if not _rate_ok(user.id):
        await q.answer("Please wait...", show_alert=True)
        return
    parts = q.data.removeprefix("rng_").split("|", 1)
    range_str = parts[0]
    country = parts[1] if len(parts) > 1 else None
    await _do_get_number(ctx, user, q.message.chat_id, range_str, country)

# ── View Ranges ─────────────────────────────────────
async def handle_view_ranges(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cfg = get_config()
    ranges = cfg.get("ranges", {})
    if not ranges:
        await update.message.reply_text("No ranges saved yet.")
        return
    buttons = []
    for country, info in ranges.items():
        flag = info.get("flag", "🏳️")
        code = info.get("code", "")
        rng = info.get("range", "")
        buttons.append([InlineKeyboardButton(
            f"{flag} {country} | {code} | {rng}",
            callback_data=f"rng_{rng}|{country}",
        )])
    await update.message.reply_text(
        "📊 <b>Saved Ranges</b>\nTap to use:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ── Contact Admin ───────────────────────────────────
async def handle_contact_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📞 Contact Admin", url=f"tg://user?id={ADMIN_ID}")]]
    )
    await update.message.reply_text("Tap below to contact admin:", reply_markup=btn)

# ── Support system ──────────────────────────────────
async def handle_support_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _support_wait.add(uid)
    await update.message.reply_text("💬 Send your message. It will be forwarded to admin.")

async def handle_support_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = update.effective_user.id
    if uid not in _support_wait:
        return False
    _support_wait.discard(uid)
    user = update.effective_user
    name = user.full_name or "Unknown"
    uname = f"@{user.username}" if user.username else "N/A"
    header = f"💬 <b>Support Message</b>\n👤 {name}\n{uname} | <code>{uid}</code>\n\n"
    try:
        await ctx.bot.send_message(ADMIN_ID, header, parse_mode=ParseMode.HTML)
        await update.message.forward(ADMIN_ID)
        await update.message.reply_text("✅ Message sent to admin.")
    except Exception:
        await update.message.reply_text("❌ Failed to send. Try again later.")
    return True

# ── Admin ───────────────────────────────────────────
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bcast")],
        [InlineKeyboardButton("⚙️ Set Range", callback_data="adm_range")],
        [InlineKeyboardButton("📊 View Ranges", callback_data="adm_viewranges")],
        [InlineKeyboardButton("📋 Logs", callback_data="adm_logs")],
    ])
    await update.message.reply_text("👑 Admin Panel", reply_markup=kb)

async def cmd_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = ctx.args
    if not args or len(args) < 3:
        await update.message.reply_text("Usage: /set Country +code rangeXXX")
        return
    country, code, rng = args[0], args[1], args[2]
    flag = flag_for(country)
    cfg = get_config()
    cfg.setdefault("ranges", {})[country] = {"code": code, "range": rng, "flag": flag}
    _save(CONFIG_FILE, cfg)
    await update.message.reply_text(f"✅ {flag} {country} {code} {rng}")

async def cmd_setchannel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /setchannel @chan1 @chan2")
        return
    cfg = get_config()
    cfg["channels"] = list(args)
    _save(CONFIG_FILE, cfg)
    await update.message.reply_text(f"✅ Channels: {', '.join(args)}")

async def cb_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        return
    action = q.data
    if action == "adm_bcast":
        _bcast_wait.add(ADMIN_ID)
        await q.message.reply_text("Send the message to broadcast (text/photo/video/file):")
    elif action == "adm_range":
        await q.message.reply_text(
            "Use command:\n/set Country +code rangeXXX\n\nExample:\n/set Tajikistan +992 99298XXX"
        )
    elif action == "adm_viewranges":
        cfg = get_config()
        ranges = cfg.get("ranges", {})
        if not ranges:
            await q.message.reply_text("No ranges saved.")
            return
        lines = ["📊 <b>All Ranges</b>\n"]
        for c, info in ranges.items():
            lines.append(f"{info.get('flag','🏳️')} {c} | {info.get('code','')} | {info.get('range','')}")
        await q.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    elif action == "adm_logs":
        data = await api_logs()
        if data:
            txt = json.dumps(data, indent=1, ensure_ascii=False)[:4000]
            await q.message.reply_text(f"<pre>{txt}</pre>", parse_mode=ParseMode.HTML)
        else:
            await q.message.reply_text("No logs available.")

async def handle_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user.id != ADMIN_ID:
        return False
    if ADMIN_ID not in _bcast_wait:
        return False
    _bcast_wait.discard(ADMIN_ID)
    users = get_users()
    sent = failed = 0
    for uid_str in users:
        try:
            await update.message.copy(int(uid_str))
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Broadcast: {sent} sent, {failed} failed")
    return True

# ── Session cleanup ─────────────────────────────────
async def cleanup_loop():
    while True:
        await asyncio.sleep(300)
        sessions = get_sessions()
        now = time.time()
        expired = [u for u, s in sessions.items() if now - s.get("ts", 0) > 1200]
        for u in expired:
            sessions.pop(u, None)
            uid = int(u)
            if uid in _polls:
                _polls[uid].cancel()
                _polls.pop(uid, None)
            _msg_track.pop(uid, None)
        if expired:
            _save(SESSIONS_FILE, sessions)

# ── Routers ─────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    if user.id == ADMIN_ID:
        if await handle_broadcast(update, ctx):
            return
    if await handle_support_msg(update, ctx):
        return
    text = update.message.text or ""
    if text == "📲 Get Number":
        await handle_get_number(update, ctx)
    elif text == "📊 View Ranges":
        await handle_view_ranges(update, ctx)
    elif text == "📞 Contact Admin":
        await handle_contact_admin(update, ctx)
    elif text == "💬 Support":
        await handle_support_start(update, ctx)

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "check_join":
        await cb_check_join(update, ctx)
    elif data.startswith("same_"):
        await cb_same_range(update, ctx)
    elif data.startswith("rng_"):
        await cb_use_range(update, ctx)
    elif data.startswith("adm_"):
        await cb_admin(update, ctx)

# ── Main ────────────────────────────────────────────
async def post_init(app: Application):
    asyncio.create_task(cleanup_loop())

async def post_shutdown(app: Application):
    await close_http()
    for t in _polls.values():
        t.cancel()

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("set", cmd_set))
    app.add_handler(CommandHandler("setchannel", cmd_setchannel))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    log.warning("Bot v2 started")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()