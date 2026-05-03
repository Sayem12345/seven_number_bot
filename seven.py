#!/usr/bin/env python3
"""Telegram OTP Number Bot - Optimized for Termux"""

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

# ── Flags ───────────────────────────────────────────
FLAGS = {
    "tajikistan": "🇹🇯", "russia": "🇷🇺", "uzbekistan": "🇺🇿",
    "kazakhstan": "🇰🇿", "kyrgyzstan": "🇰🇬", "india": "🇮🇳",
    "pakistan": "🇵🇰", "bangladesh": "🇧🇩", "indonesia": "🇮🇩",
    "usa": "🇺🇸", "uk": "🇬🇧", "turkey": "🇹🇷", "iran": "🇮🇷",
    "china": "🇨🇳", "brazil": "🇧🇷", "nigeria": "🇳🇬",
    "afghanistan": "🇦🇫", "egypt": "🇪🇬", "germany": "🇩🇪",
}

def flag_for(country):
    return FLAGS.get(country.lower(), "🏳️")

# ── Concurrency guards ──────────────────────────────
_polls: dict[int, asyncio.Task] = {}
_locks: dict[int, asyncio.Lock] = {}
_rl: dict[int, float] = {}
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

# ── API Client ──────────────────────────────────────
async def api_get_number(range_str: str) -> dict | None:
    body = {"range": range_str, "format": "national"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{API_BASE}/numbers/get", json=body,
                headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                if r.status == 200:
                    return await r.json()
                log.warning("get_number %s: %s", r.status, await r.text())
    except Exception as e:
        log.warning("get_number err: %s", e)
    return None

async def api_get_sms(number_id: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{API_BASE}/numbers/{number_id}/sms",
                headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    return await r.json()
    except Exception as e:
        log.warning("get_sms err: %s", e)
    return None

async def api_logs(limit=50) -> dict | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{API_BASE}/console/logs", params={"limit": limit},
                headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
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

# ── Admin notify ────────────────────────────────────
async def notify_admin(ctx, user, number="", otp=""):
    name = getattr(user, "full_name", "Unknown")
    uname = f"@{user.username}" if getattr(user, "username", None) else "N/A"
    lines = [f"👤 {name}", f"{uname} | <code>{user.id}</code>", ""]
    if number:
        lines.append(f"Number - <code>{number}</code>")
    if otp:
        lines.append(f"OTP - <code>{otp}</code>")
    try:
        await ctx.bot.send_message(ADMIN_ID, "\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("notify err: %s", e)

# ── OTP polling ─────────────────────────────────────
async def poll_otp(ctx, uid: int, user, number_id: str, number: str):
    try:
        for _ in range(600):
            data = await api_get_sms(number_id)
            if data:
                status = data.get("status", "")
                if status == "success":
                    otp = (
                        data.get("otp")
                        or data.get("code")
                        or data.get("sms", "")
                    )
                    if not otp and "text" in data:
                        m = re.search(r"\b(\d{4,8})\b", data["text"])
                        if m:
                            otp = m.group(1)
                    text = (
                        f"Number - <code>{number}</code>\n"
                        f"OTP - <code>{otp}</code>"
                    )
                    try:
                        await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML)
                    except Exception:
                        pass
                    await notify_admin(ctx, user, number, str(otp))
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
    kb = ReplyKeyboardMarkup([["📲 Get Number"]], resize_keyboard=True)
    await update.message.reply_text("Welcome! Tap below to get a number.", reply_markup=kb)

async def cb_check_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ok, _ = await check_joined(ctx, q.from_user.id)
    if not ok:
        await q.answer("You haven't joined all channels yet.", show_alert=True)
        return
    kb = ReplyKeyboardMarkup([["📲 Get Number"]], resize_keyboard=True)
    await q.message.reply_text("Welcome! Tap below to get a number.", reply_markup=kb)

# ── Get number ──────────────────────────────────────
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
    if not country:
        country = "Unknown"

    async with _lock(user.id):
        data = await api_get_number(range_str)

    if not data or "number" not in data:
        await ctx.bot.send_message(chat_id, "❌ Failed to get number. Try again.")
        return

    number = data["number"]
    nid = data["number_id"]
    save_session(user.id, {
        "number_id": nid, "number": number,
        "range": range_str, "country": country, "ts": time.time(),
    })

    text = f"Number - <code>{number}</code>"
    btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Same Range", callback_data=f"same_{range_str}")]]
    )
    await ctx.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, reply_markup=btn)
    await notify_admin(ctx, user, number)
    task = asyncio.create_task(poll_otp(ctx, user.id, user, nid, number))
    _polls[user.id] = task

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

# ── Admin ───────────────────────────────────────────
_bcast_wait: set[int] = set()

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bcast")],
        [InlineKeyboardButton("⚙️ Set Range", callback_data="adm_range")],
        [InlineKeyboardButton("📋 Logs", callback_data="adm_logs")],
    ])
    await update.message.reply_text("Admin Panel", reply_markup=kb)

async def cmd_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = ctx.args
    if not args or len(args) < 3:
        await update.message.reply_text("Usage: /set Country +code rangeXXX")
        return
    country, code, rng = args[0], args[1], args[2]
    cfg = get_config()
    cfg.setdefault("ranges", {})[country] = {
        "code": code, "range": rng, "flag": flag_for(country),
    }
    _save(CONFIG_FILE, cfg)
    await update.message.reply_text(f"✅ {flag_for(country)} {country} {code} {rng}")

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
async def cleanup_loop(_: Application):
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
        if expired:
            _save(SESSIONS_FILE, sessions)

# ── Routers ─────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if update.effective_user.id == ADMIN_ID:
        if await handle_broadcast(update, ctx):
            return
    text = update.message.text or ""
    if text == "📲 Get Number":
        await handle_get_number(update, ctx)

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "check_join":
        await cb_check_join(update, ctx)
    elif data.startswith("same_"):
        await cb_same_range(update, ctx)
    elif data.startswith("adm_"):
        await cb_admin(update, ctx)

# ── Main ────────────────────────────────────────────
async def post_init(app: Application):
    asyncio.create_task(cleanup_loop(app))

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("set", cmd_set))
    app.add_handler(CommandHandler("setchannel", cmd_setchannel))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    log.warning("Bot started")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
