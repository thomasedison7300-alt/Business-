
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
print("""

╔══════════════════════════════════════════════════════════╗
║                        E L   Z O Z                       ║
║                   TELEGRAM BUSINESS BOT                  ║
║                     DEV BY : @Z0_E0                      ║
╚══════════════════════════════════════════════════════════╝
""")
import os
from pathlib import Path
import asyncio
import aiosqlite
import sqlite3
import zipfile
from datetime import datetime, timezone, timedelta
import html
import re
import json
from urllib.parse import urlparse
import logging
import unicodedata
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BusinessConnection, BusinessMessagesDeleted, ChatMemberUpdated, CopyTextButton,
    KeyboardButton, ReplyKeyboardMarkup, BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

# ════════════════════ إعدادات التشغيل — عدّل القيم هنا مباشرة ════════════════════
# أي قيمة تتركها فارغة "" يقرأها البوت من ملف .env (لو موجود) كما كان قبل التعديل.
CFG_BOT_TOKEN = "8719220845:AAFHxIXqUKSpODCBEVm923KFsSnHJDwkQ2o"
CFG_OWNER_ID = "6604178348"
CFG_VIRUSTOTAL_API_KEY = "dba78a858bf9172f15041d49725b21ea9c16949488855a9237d5b880d123cad4"   # مفتاح VirusTotal كاملًا
# Truecaller
CFG_TC_API_ID = "32436466"
CFG_TC_API_HASH = "ede40edc665c6b2602c2b207a93db691"
CFG_TC_SESSION = ""           # الجلسة كاملة
# Rich Messages: 1 تشغيل / 0 إيقاف — والفحص يبعت رسائل اختبار للمالك عند التشغيل
CFG_RICH_MESSAGES = "1"
CFG_RICH_PROBE = "0"          # "1" = يبعت رسائل فحص للمالك عند التشغيل (موقوف)
CFG_RICH_NOTIFY = "1"         # "0" = لا يبعتلك إخطارات ⚠️ Rich عند رفض غير متوقع
for _k, _v in (("BOT_TOKEN", CFG_BOT_TOKEN), ("OWNER_ID", CFG_OWNER_ID),
               ("VIRUSTOTAL_API_KEY", CFG_VIRUSTOTAL_API_KEY), ("TC_API_ID", CFG_TC_API_ID),
               ("TC_API_HASH", CFG_TC_API_HASH), ("TC_SESSION", CFG_TC_SESSION),
               ("RICH_MESSAGES", CFG_RICH_MESSAGES), ("RICH_PROBE", CFG_RICH_PROBE), ("RICH_NOTIFY", CFG_RICH_NOTIFY)):
    if str(_v).strip():
        os.environ[_k] = str(_v).strip()
# ═══════════════════════════════════════════════════════════════════════════════
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
# بيانات التشغيل تُقرأ من ملف .env ولا تُحفظ داخل الكود.
TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID_RAW = os.getenv("OWNER_ID", "6604178348").strip()
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
# بيانات Truecaller اختيارية؛ اترك TC_SESSION فارغًا لتعطيل الميزة.
TC_API_ID = os.getenv("TC_API_ID", "").strip()
TC_API_HASH = os.getenv("TC_API_HASH", "").strip()
TC_SESSION = os.getenv("TC_SESSION", "").strip()
TC_BOT_USERNAME = "TrueCalleRobot"
_tc_client = None
_tc_lock = asyncio.Lock()
BOT_NAME = os.getenv("BOT_NAME", "EL ZOZ").strip() or "EL ZOZ"
DB = os.getenv("DB_PATH", "nexus_code.db")
BOT_CHANNEL_URL = os.getenv("BOT_CHANNEL_URL", "https://t.me/Z0_E7").strip()
DEVELOPER_CHANNEL_URL = os.getenv("DEVELOPER_CHANNEL_URL", "https://t.me/elzoz_mrkt").strip()
DEVELOPER_URL = os.getenv("DEVELOPER_URL", "https://t.me/Z0_E9").strip()
PROTECTED_MUTE_USER_IDS = ()
PROTECTED_MUTE_USER_ID_SET = set(PROTECTED_MUTE_USER_IDS)
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
if not TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود. أضف توكن البوت إلى ملف .env")
try:
    OWNER_ID = int(OWNER_ID_RAW)
except ValueError as exc:
    raise RuntimeError("ضع OWNER_ID رقميًا داخل ملف .env") from exc
PROTECTED_MUTE_USER_ID_SET.add(OWNER_ID)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("nexus_bot")

router = Router()
WELCOME_COOLDOWN = timedelta(hours=1)

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
class ReplySG(StatesGroup):
    add_trigger = State()
    add_response = State()
    ask_buttons = State()
    btn_label = State()
    btn_type = State()
    btn_color = State()
    btn_value = State()
    ask_more = State()
    edit_trigger = State()
    edit_response = State()

class WordSG(StatesGroup):
    add_word = State()
    edit_word = State()

class ForceSG(StatesGroup):
    add_channel = State()
    add_title = State()
    edit_channel = State()
    edit_title = State()

class BroadcastSG(StatesGroup):
    add_text = State()

class BotBroadcastSG(StatesGroup):
    add_text = State()

class ChannelBroadcastSG(StatesGroup):
    add_text = State()

class WelcomeSG(StatesGroup):
    set_text = State()
    ask_buttons = State()
    btn_label = State()
    btn_type = State()
    btn_value = State()
    btn_color = State()
    ask_more = State()
    ask_image = State()
    ask_mode = State()
    set_sticker = State()
    set_image = State()

class MuteSG(StatesGroup):
    chat_id = State()

class AdminSG(StatesGroup):
    add_admin = State()
    ban_user_id = State()
    unban_user_id = State()
    edit_user_id = State()
    edit_user_name = State()
    bot_welcome_image = State()
    edit_bot_message = State()
    restore_backup = State()

class SubscriptionSG(StatesGroup):
    user_id = State()
    duration = State()

class SocialSG(StatesGroup):
    choose = State()
    value = State()

class MediaSG(StatesGroup):
    dashboard_video = State()

class PaymentSG(StatesGroup):
    network = State()
    value = State()

class LiveBioSG(StatesGroup):
    add_verse = State()
    
PAYMENT_METHODS = {
    "bybit": {"name": "باي بيت", "emoji": "5199662703332836840", "fallback": "💳", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ باي بيت الآن:", "aliases": ("باي بيت", "بايبيت", "Bybit", "Paybit")},
    "binance": {"name": "Binance", "emoji": "5454205576512818013", "fallback": "🟡", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ Binance الآن:", "aliases": ("Binance", "باينانس", "بينانس")},
    "shamcash": {"name": "شام كاش", "emoji": "5974562373619424507", "fallback": "💸", "prompt": "أرسل عنوان شام كاش الآن (الحروف والأرقام فقط):", "aliases": ("شام كاش", "شامكاش", "Sham Cash", "ShamCash"), "alnum_only": True},
    "iraqi_master": {"name": "ماستر عراقي", "emoji": "5190642511802022990", "fallback": "💳", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ ماستر عراقي الآن:", "aliases": ("ماستر عراقي", "ماسترعراقي", "Master Iraqi", "Iraqi Master")},
    "zaincash": {"name": "زين كاش", "emoji": "5226459773091731013", "fallback": "📱", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ زين كاش الآن:", "aliases": ("زين كاش", "زينكاش", "Zain Cash", "ZainCash")},
    "asiasel": {"name": "آسياسيل", "emoji": "5388668704902895822", "fallback": "📱", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ آسياسيل الآن:", "aliases": ("آسياسيل", "اسيا سيل", "اساسيل", "Asiacell")},
    "orange": {"name": "اورنج كاش", "emoji": "5836714629455157161", "fallback": "🟠", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ اورنج كاش الآن:", "aliases": ("اورنج كاش", "اورنج", "أورنج كاش", "أورنج", "Orange Cash", "Orange")},
    "we": {"name": "وي كاش", "emoji": "5837128389424585193", "fallback": "🟣", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ وي كاش الآن:", "aliases": ("وي كاش", "وي", "WE Cash", "WE", "We Cash", "We")},
    "etisalat": {"name": "اتصالات كاش", "emoji": "5836811137370297987", "fallback": "📶", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ اتصالات كاش الآن:", "aliases": ("اتصالات كاش", "اتصالات", "اتصلات كاش", "اتصلات", "Etisalat Cash", "Etisalat", "EG")},
    "vodafone": {"name": "فودافون كاش", "emoji": "5834628314731387616", "fallback": "📱", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ فودافون كاش الآن:", "aliases": ("فودافون", "فودافون كاش", "فودا", "Vodafone", "Vodafone Cash", "Voda")},
    "tonkeeper": {"name": "تون كيبر", "emoji": "5424905554432631390", "fallback": "💎", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ Tonkeeper الآن:", "aliases": ("تون كيبر", "تونكيبر", "Tonkeeper", "Ton Keeper")},
    "gram": {"name": "GRAM (TON)", "emoji": "5240164592826469263", "fallback": "🪙", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ Gram (TON) الآن:", "network_required": True, "network_prompt": "أرسل اسم الشبكة لعملة Gram (TON) أولًا:\nمثال: TRC20 أو ERC20 أو BEP20 أو TON", "aliases": ("GRAM", "GRAM TON", "GRAM (TON)", "جرام", "جرام تون", "جرام (تون)")},
    "usdt": {"name": "USDT", "emoji": "5080137014775383220", "fallback": "💵", "prompt": "أرسل البيانات (الأيدي/الرقم/العنوان) لـ USDT الآن:", "network_required": True, "network_prompt": "أرسل اسم الشبكة لعملة USDT أولًا:\nمثال: TRC20 أو ERC20 أو BEP20 أو TON", "aliases": ("USDT", "تيثر", "Tether")},
}
PAYMENT_ENTRY_ORDER = ("bybit", "binance", "shamcash", "iraqi_master", "zaincash", "asiasel", "egypt_group", "tonkeeper", "gram", "usdt")
PAYMENT_EGYPT_ORDER = ("orange", "we", "etisalat", "vodafone")
PAYMENT_CUSTOMER_NAMES = {
    "orange": "اورنج كاش",
    "we": "وي كاش",
    "etisalat": "اتصالات كاش",
    "vodafone": "فودافون كاش",
}
PAYMENT_GROUP = {"name": "شبكات مصرية", "emoji": "5976310790381115423", "fallback": "📱"}

def normalize_payment_phrase(value):
    value = (value or "").strip().casefold().translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    return re.sub(r"[^\w]", "", value, flags=re.UNICODE)

PAYMENT_TRIGGER_MAP = {
    normalize_payment_phrase(alias): key
    for key, info in PAYMENT_METHODS.items()
    for alias in info["aliases"]
}

def match_payment_method(value):
    return PAYMENT_TRIGGER_MAP.get(normalize_payment_phrase(value))

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
_SAFE_COLUMN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def safe_column(name: str) -> str:
    if not isinstance(name, str) or not _SAFE_COLUMN_RE.match(name):
        raise ValueError(f"Invalid column name: {name!r}")
    return name

async def db():
    conn = await aiosqlite.connect(DB)
    conn.row_factory = aiosqlite.Row
    return conn

async def fetchone(conn, query, params=()):
    cur = await conn.execute(query, params)
    return await cur.fetchone()

async def init_db():
    conn = await db()
    await conn.executescript("""
    CREATE TABLE IF NOT EXISTS settings(
        owner_id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 1,
        welcome TEXT DEFAULT '',
        welcome_buttons TEXT DEFAULT '[]',
        media_file_id TEXT DEFAULT '',
        media_type TEXT DEFAULT '',
        dashboard_video_file_id TEXT DEFAULT '',
        dashboard_video_type TEXT DEFAULT '',
        welcome_enabled INTEGER DEFAULT 1,
        welcome_mode TEXT DEFAULT 'always',
        social_enabled INTEGER DEFAULT 1,
        social_tiktok TEXT DEFAULT '',
        social_instagram TEXT DEFAULT '',
        social_telegram TEXT DEFAULT '',
        social_facebook TEXT DEFAULT '',
        social_youtube TEXT DEFAULT '',
        media_enabled INTEGER DEFAULT 1,
        media_delete_types TEXT DEFAULT '[]'
        ,welcome_sticker_file_id TEXT DEFAULT '',
        welcome_image_file_id TEXT DEFAULT '',
        welcome_image_type TEXT DEFAULT '',
        bot_welcome_image_file_id TEXT DEFAULT '',
        bot_welcome_image_type TEXT DEFAULT '',
        track_deleted_enabled INTEGER DEFAULT 1,
        track_edited_enabled INTEGER DEFAULT 1,
        transfer_enabled INTEGER DEFAULT 1,
        calculator_enabled INTEGER DEFAULT 1,
        currency_enabled INTEGER DEFAULT 1,
        live_clock_enabled INTEGER DEFAULT 0,
        live_clock_style INTEGER DEFAULT 0,
        live_bio_enabled INTEGER DEFAULT 0,
        live_bio_religion TEXT DEFAULT '',
        live_bio_verses TEXT DEFAULT '',
        live_bio_custom_verses TEXT DEFAULT '{}',
        live_bio_custom_texts TEXT DEFAULT '[]',
        live_bio_mode TEXT DEFAULT 'custom',
        live_bio_mode_migrated INTEGER DEFAULT 0,
        live_bio_interval_minutes INTEGER DEFAULT 360,
        live_bio_custom_interval_minutes INTEGER DEFAULT 360,
        live_bio_religious_interval_minutes INTEGER DEFAULT 360,
        live_bio_last_updated INTEGER DEFAULT 0,
        live_bio_index INTEGER DEFAULT 0,
        bot_force_enabled INTEGER DEFAULT 1,
        bot_access_mode TEXT DEFAULT 'free',
        bot_trial_hours INTEGER DEFAULT 24,
        account_force_enabled INTEGER DEFAULT 1,
        replies_enabled INTEGER DEFAULT 1,
        words_enabled INTEGER DEFAULT 1,
        muted_enabled INTEGER DEFAULT 1,
        payment_enabled INTEGER DEFAULT 1,
        broadcast_enabled INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS business(
        connection_id TEXT PRIMARY KEY,
        user_id INTEGER,
        enabled INTEGER DEFAULT 1,
        can_reply INTEGER DEFAULT 0,
        original_name TEXT DEFAULT '',
        original_last_name TEXT DEFAULT NULL,
        clock_enabled INTEGER DEFAULT 0,
        clock_style INTEGER DEFAULT 0,
        can_edit_name INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS payment_wallets(
        owner_id INTEGER NOT NULL,
        wallet_key TEXT NOT NULL,
        wallet_value TEXT NOT NULL DEFAULT '',
        network TEXT NOT NULL DEFAULT '',
        enabled INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL DEFAULT '',
        PRIMARY KEY(owner_id, wallet_key)
    );
    CREATE TABLE IF NOT EXISTS customers(
        connection_id TEXT,
        chat_id INTEGER,
        first_name TEXT,
        username TEXT,
        last_seen TEXT,
        last_welcome TEXT DEFAULT '',
        last_subscription_prompt_id INTEGER DEFAULT 0,
        PRIMARY KEY(connection_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS bot_users(
        user_number INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        first_name TEXT DEFAULT '',
        username TEXT DEFAULT '',
        first_seen TEXT NOT NULL,
        blocked INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS bot_subscriptions(
        user_id INTEGER PRIMARY KEY,
        expires_at TEXT NOT NULL,
        trial INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS bot_channels(
        chat_id INTEGER PRIMARY KEY,
        title TEXT DEFAULT '',
        username TEXT DEFAULT '',
        added_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS replies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        trigger TEXT,
        response TEXT
    );
    CREATE TABLE IF NOT EXISTS reply_buttons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reply_id INTEGER,
        label TEXT,
        btn_type TEXT,
        btn_color TEXT DEFAULT 'primary',
        icon_custom_emoji_id TEXT DEFAULT '',
        btn_value TEXT,
        position INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS banned_words(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        word TEXT
    );
    CREATE TABLE IF NOT EXISTS muted(
        connection_id TEXT,
        chat_id INTEGER,
        PRIMARY KEY(connection_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS violations(
        connection_id TEXT,
        chat_id INTEGER,
        owner_id INTEGER,
        count INTEGER DEFAULT 0,
        last_word TEXT DEFAULT '',
        updated_at TEXT,
        PRIMARY KEY(connection_id, chat_id)
    );
    CREATE TABLE IF NOT EXISTS force_channels(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        channel TEXT,
        title TEXT,
        scope TEXT DEFAULT 'account'
    );
    CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY,
        added_at TEXT
    );
    CREATE TABLE IF NOT EXISTS bot_messages(
        message_key TEXT PRIMARY KEY,
        text TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS account_messages(
        owner_id INTEGER NOT NULL,
        message_key TEXT NOT NULL,
        text TEXT NOT NULL DEFAULT '',
        PRIMARY KEY(owner_id, message_key)
    );
    CREATE TABLE IF NOT EXISTS tracking_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        connection_id TEXT NOT NULL,
        chat_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        old_text TEXT DEFAULT '',
        new_text TEXT DEFAULT '',
        media_type TEXT DEFAULT '',
        media_file_id TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tracked_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        connection_id TEXT,
        chat_id INTEGER,
        message_id INTEGER,
        sender_id INTEGER,
        sender_name TEXT,
        sender_username TEXT,
        text_content TEXT,
        media_type TEXT,
        media_file_id TEXT,
        created_at TEXT,
        UNIQUE(connection_id, chat_id, message_id)
    );
    """)
    try:
        await conn.execute("ALTER TABLE reply_buttons ADD COLUMN icon_custom_emoji_id TEXT DEFAULT ''")
    except Exception:
        pass
    for column, definition in [
        ("dashboard_video_file_id", "TEXT DEFAULT ''"),
        ("dashboard_video_type", "TEXT DEFAULT ''"),
        ("welcome_enabled", "INTEGER DEFAULT 1"),
        ("welcome_mode", "TEXT DEFAULT 'always'"),
        ("welcome_buttons", "TEXT DEFAULT '[]'"),
        ("social_enabled", "INTEGER DEFAULT 1"),
        ("social_tiktok", "TEXT DEFAULT ''"),
        ("social_instagram", "TEXT DEFAULT ''"),
        ("social_telegram", "TEXT DEFAULT ''"),
        ("social_facebook", "TEXT DEFAULT ''"),
        ("social_youtube", "TEXT DEFAULT ''"),
        ("media_enabled", "INTEGER DEFAULT 1"),
        ("media_delete_types", "TEXT DEFAULT '[]'"),
        ("welcome_sticker_file_id", "TEXT DEFAULT ''"),
        ("welcome_image_file_id", "TEXT DEFAULT ''"),
        ("welcome_image_type", "TEXT DEFAULT ''"),
        ("bot_welcome_image_file_id", "TEXT DEFAULT ''"),
        ("bot_welcome_image_type", "TEXT DEFAULT ''"),
        ("track_deleted_enabled", "INTEGER DEFAULT 1"),
        ("track_edited_enabled", "INTEGER DEFAULT 1"),
        ("transfer_enabled", "INTEGER DEFAULT 1"),
        ("calculator_enabled", "INTEGER DEFAULT 1"),
        ("currency_enabled", "INTEGER DEFAULT 1"),
        ("live_clock_enabled", "INTEGER DEFAULT 0"),
        ("live_clock_style", "INTEGER DEFAULT 0"),
        ("live_bio_enabled", "INTEGER DEFAULT 0"),
        ("live_bio_religion", "TEXT DEFAULT ''"),
        ("live_bio_verses", "TEXT DEFAULT ''"),
        ("live_bio_custom_verses", "TEXT DEFAULT '{}'"),
        ("live_bio_custom_texts", "TEXT DEFAULT '[]'"),
        ("live_bio_mode", "TEXT DEFAULT 'custom'"),
        ("live_bio_mode_migrated", "INTEGER DEFAULT 0"),
        ("live_bio_interval_minutes", "INTEGER DEFAULT 360"),
        ("live_bio_custom_interval_minutes", "INTEGER DEFAULT 0"),
        ("live_bio_religious_interval_minutes", "INTEGER DEFAULT 0"),
        ("live_bio_last_updated", "INTEGER DEFAULT 0"),
        ("live_bio_index", "INTEGER DEFAULT 0"),
        ("bot_force_enabled", "INTEGER DEFAULT 1"),
        ("bot_access_mode", "TEXT DEFAULT 'free'"),
        ("bot_trial_hours", "INTEGER DEFAULT 24"),
        ("account_force_enabled", "INTEGER DEFAULT 1"),
        ("replies_enabled", "INTEGER DEFAULT 1"),
        ("words_enabled", "INTEGER DEFAULT 1"),
        ("muted_enabled", "INTEGER DEFAULT 1"),
        ("payment_enabled", "INTEGER DEFAULT 1"),
        ("broadcast_enabled", "INTEGER DEFAULT 1"),
    ]:
        try:
            await conn.execute(f"ALTER TABLE settings ADD COLUMN {column} {definition}")
        except Exception:
            pass
    await conn.execute(
        "UPDATE settings SET live_bio_custom_interval_minutes=COALESCE(NULLIF(live_bio_interval_minutes, 0), 360) "
        "WHERE live_bio_custom_interval_minutes IS NULL OR live_bio_custom_interval_minutes<=0"
    )
    await conn.execute(
        "UPDATE settings SET live_bio_religious_interval_minutes=COALESCE(NULLIF(live_bio_interval_minutes, 0), 360) "
        "WHERE live_bio_religious_interval_minutes IS NULL OR live_bio_religious_interval_minutes<=0"
    )
    for column, definition in [
        ("original_name", "TEXT DEFAULT ''"),
        ("original_last_name", "TEXT DEFAULT NULL"),
        ("clock_enabled", "INTEGER DEFAULT 0"),
        ("clock_style", "INTEGER DEFAULT 0"),
        ("can_edit_name", "INTEGER DEFAULT 0"),
        ("can_edit_bio", "INTEGER DEFAULT 0"),
    ]:
        try:
            await conn.execute(f"ALTER TABLE business ADD COLUMN {column} {definition}")
        except Exception:
            pass
    try:
        await conn.execute("ALTER TABLE bot_users ADD COLUMN blocked INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        await conn.execute("ALTER TABLE customers ADD COLUMN last_subscription_prompt_id INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        await conn.execute("ALTER TABLE force_channels ADD COLUMN scope TEXT DEFAULT 'account'")
    except Exception:
        pass
    try:
        bio_rows = await conn.execute_fetchall(
            "SELECT owner_id, live_bio_religion, live_bio_verses, live_bio_custom_verses FROM settings"
        )
        for bio_row in bio_rows:
            religion = bio_row["live_bio_religion"] or ""
            if religion not in LIVE_BIO_NAMES:
                continue
            try:
                custom_map = json.loads(bio_row["live_bio_custom_verses"] or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                custom_map = {}
            if not isinstance(custom_map, dict):
                custom_map = {}
            if religion in custom_map:
                continue
            try:
                old_verses = json.loads(bio_row["live_bio_verses"] or "[]")
            except (TypeError, ValueError, json.JSONDecodeError):
                old_verses = []
            defaults = set(LIVE_BIO_DEFAULTS.get(religion, []))
            custom_map[religion] = [
                str(item).strip() for item in old_verses
                if str(item).strip() and str(item).strip() not in defaults
            ] if isinstance(old_verses, list) else []
            await conn.execute(
                "UPDATE settings SET live_bio_custom_verses=? WHERE owner_id=?",
                (json.dumps(custom_map, ensure_ascii=False), bio_row["owner_id"]),
            )
    except Exception:
        logger.exception("Failed to migrate old live-bio custom entries")

    try:
        mode_rows = await conn.execute_fetchall(
            "SELECT owner_id, live_bio_religion, live_bio_mode, live_bio_mode_migrated FROM settings"
        )
        for mode_row in mode_rows:
            if mode_row["live_bio_mode_migrated"]:
                continue
            religion = mode_row["live_bio_religion"] or ""
            mode = "religious" if religion in LIVE_BIO_NAMES else (mode_row["live_bio_mode"] or "custom")
            await conn.execute(
                "UPDATE settings SET live_bio_mode=?, live_bio_mode_migrated=1 WHERE owner_id=?",
                (mode, mode_row["owner_id"]),
            )
    except Exception:
        logger.exception("Failed to migrate live-bio mode")

    await conn.execute(
        "UPDATE force_channels SET scope='bot' WHERE owner_id=? AND (scope IS NULL OR scope='account')",
        (OWNER_ID,)
    )
    await conn.execute(
        "INSERT OR IGNORE INTO settings(owner_id, enabled, welcome) VALUES(?, ?, ?)",
        (OWNER_ID, 1, "")
    )
    await conn.commit()
    await conn.close()

async def is_admin(user_id: int) -> bool:
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT 1 FROM business WHERE user_id=? AND enabled=1 LIMIT 1",
        (user_id,)
    )
    if not row:
        row = await fetchone(conn, "SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    if not row and user_id == OWNER_ID:
        row = True
    await conn.close()
    return bool(row)

async def is_account_linked(user_id: int) -> bool:
    """هل لدى المستخدم اتصال Telegram Business مفعّل بهذا البوت؟"""
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT 1 FROM business WHERE user_id=? AND enabled=1 LIMIT 1",
        (user_id,)
    )
    await conn.close()
    return bool(row)

async def get_setting(key: str):
    conn = await db()
    row = await fetchone(conn, f"SELECT {safe_column(key)} FROM settings WHERE owner_id=?", (OWNER_ID,))
    await conn.close()
    return row[key] if row else None

async def set_setting(key: str, value):
    conn = await db()
    await conn.execute(f"UPDATE settings SET {safe_column(key)}=? WHERE owner_id=?", (value, OWNER_ID))
    await conn.commit()
    await conn.close()

BOT_MESSAGE_DEFAULTS = {
    "welcome": "<blockquote><tg-emoji emoji-id='5985478698722136468'>👋</tg-emoji> <b>أهلاً بك يا {name}</b>\n\n<tg-emoji emoji-id='6032999834772139200'>👤</tg-emoji> أنا مساعدك الشخصي لإدارة حسابك باحترافية وهدوء.</blockquote>",
    "bot_force_sub": BOT_FORCE_SUB_TEXT if "BOT_FORCE_SUB_TEXT" in globals() else "يجب الاشتراك في القنوات التالية:",
    "account_force_sub": ACCOUNT_FORCE_SUB_TEXT if "ACCOUNT_FORCE_SUB_TEXT" in globals() else "لإكمال المحادثة، اشترك أولاً في القنوات التالية:",
    "link_help": "<b>اربط حسابك خلال دقائق</b>\n\nاتبع التعليمات الموجودة بالأسفل.",
}

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

async def get_bot_message(key):
    conn = await db()
    row = await fetchone(conn, "SELECT text FROM bot_messages WHERE message_key=?", (key,))
    await conn.close()
    if row and row["text"]:
        return row["text"]
    return BOT_MESSAGE_DEFAULTS.get(key, "")

async def set_bot_message(key, text):
    conn = await db()
    await conn.execute("INSERT INTO bot_messages(message_key,text) VALUES(?,?) ON CONFLICT(message_key) DO UPDATE SET text=excluded.text", (key, text))
    await conn.commit(); await conn.close()

async def get_account_message(owner_id, key):
    conn=await db(); row=await fetchone(conn, "SELECT text FROM account_messages WHERE owner_id=? AND message_key=?", (owner_id,key)); await conn.close()
    return row["text"] if row and row["text"] else await get_bot_message(key)

async def set_account_message(owner_id, key, text):
    conn=await db(); await conn.execute("INSERT INTO account_messages(owner_id,message_key,text) VALUES(?,?,?) ON CONFLICT(owner_id,message_key) DO UPDATE SET text=excluded.text", (owner_id,key,text)); await conn.commit(); await conn.close()

async def ensure_account_settings(owner_id: int):
    conn = await db()
    await conn.execute("INSERT OR IGNORE INTO settings(owner_id, enabled, welcome) VALUES(?, 1, '')", (owner_id,))
    await conn.commit()
    await conn.close()

async def settings_owner(user_id: int) -> int:
    return user_id if await is_account_linked(user_id) else OWNER_ID

async def get_account_setting(owner_id: int, key: str):
    conn = await db()
    row = await fetchone(conn, f"SELECT {safe_column(key)} FROM settings WHERE owner_id=?", (owner_id,))
    await conn.close()
    return row[key] if row else None

async def set_account_setting(owner_id: int, key: str, value):
    await ensure_account_settings(owner_id)
    conn = await db()
    await conn.execute(f"UPDATE settings SET {safe_column(key)}=? WHERE owner_id=?", (value, owner_id))
    await conn.commit()
    await conn.close()
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
BTN_STYLE_MAP = {
    "danger": "danger",
    "success": "success",
    "primary": "primary",
}

STYLE_LABEL = {
    "danger": "أحمر",
    "success": "أخضر",
    "primary": "أزرق",
}

def safe_html(v):
    return html.escape(str(v or ""), quote=False)

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

BOT_OK_EMOJI = "6206479140040743133"
BOT_DANGER_EMOJI = "6206110936789423908"
BOT_INFO_EMOJI = "5904219717073114606"
BOT_HOME_EMOJI = "5445365692004071819"
BOT_USER_EMOJI = "5985478698722136468"

def fancy_success(text):
    return f"<blockquote><tg-emoji emoji-id='{BOT_OK_EMOJI}'>✅</tg-emoji> <b>{text}</b></blockquote>"

def fancy_error(text):
    return f"<blockquote><tg-emoji emoji-id='{BOT_DANGER_EMOJI}'>⚠️</tg-emoji> <b>{text}</b></blockquote>"

def fancy_info(text):
    return f"<blockquote><tg-emoji emoji-id='{BOT_INFO_EMOJI}'>✦</tg-emoji> <b>{text}</b></blockquote>"

async def edit_or_replace(call, text, reply_markup=None):
    try:
        await call.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

def public_kb(user_id=None):
    rows = []
    channel_row = []
    if BOT_CHANNEL_URL:
        channel_row.append(InlineKeyboardButton(
            text="قناة البوت", url=BOT_CHANNEL_URL,
            style="primary", icon_custom_emoji_id="5258093637450866522"
        ))
    if DEVELOPER_CHANNEL_URL:
        channel_row.append(InlineKeyboardButton(
            text="قناة المطور", url=DEVELOPER_CHANNEL_URL,
            style="primary", icon_custom_emoji_id="5258260149037965799"
        ))
    if channel_row:
        rows.append(channel_row)
    if DEVELOPER_URL:
        rows.append([InlineKeyboardButton(
            text="𓏺 𝖤𝖫 𝖹𝖮𝖹 .", url=DEVELOPER_URL,
            style="success", icon_custom_emoji_id="6206155797722830770"
        )])
    rows.append([InlineKeyboardButton(
        text="لوحة التحكم", callback_data="control_panel",
        style="primary", icon_custom_emoji_id="5445128296276718145"
    )])
    if user_id == OWNER_ID:
        rows.append([InlineKeyboardButton(text="لوحة الأدمن", callback_data="admin_panel", style="primary", icon_custom_emoji_id="5789452774970236366")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def link_help_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="اذهب للاعدادات", url="tg://settings", style="primary", icon_custom_emoji_id="5447389837076231920")],
        [InlineKeyboardButton(text="رجوع", callback_data="public_home",
                              style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

async def delete_biz_msg(bot, bc_id, chat_id, message_id):
    try:
        await bot.delete_business_messages(
            business_connection_id=bc_id,
            message_ids=[message_id]
        )
    except Exception:
        logger.warning("Failed to delete business message", exc_info=True)

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

async def required_subs(bot, user_id, owner_id=OWNER_ID, scope="account"):
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT channel, title FROM force_channels WHERE owner_id=? AND scope=? ORDER BY id",
        (owner_id, scope)
    )
    await conn.close()
    missing = []
    for row in rows:
        try:
            member = await bot.get_chat_member(chat_id=row["channel"], user_id=user_id)
            if member.status in {"left", "kicked"}:
                missing.append((row["channel"], row["title"]))
        except Exception:
            logger.warning("Could not verify required channel %s", row["channel"], exc_info=True)
    return missing

def sub_kb(channels):
    rows = []
    for ch, title in channels:
        if str(ch).startswith("@"):
            rows.append([InlineKeyboardButton(
                text=f"اشترك في {title}",
                url=f"https://t.me/{str(ch)[1:]}",
                style="primary", icon_custom_emoji_id="6041685260687642937"
            )])
    rows.append([InlineKeyboardButton(
        text="تحقق من الاشتراك",
        callback_data="account_force_verify",
        style="success",
        icon_custom_emoji_id="6206479140040743133"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

def bot_sub_kb(channels):
    rows = []
    for ch, title in channels:
        if str(ch).startswith("@"):
            rows.append([InlineKeyboardButton(
                text=f"اشترك في {title}",
                url=f"https://t.me/{str(ch)[1:]}",
                style="primary", icon_custom_emoji_id="5444988177263654261"
            )])
    rows.append([InlineKeyboardButton(
        text="تحقق من الاشتراك",
        callback_data="bot_force_verify",
        style="success",
        icon_custom_emoji_id="6206479140040743133"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

BOT_FORCE_SUB_TEXT = (
    "<blockquote><tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> "
    "<b>خطوة واحدة تفصلك عن البدء</b>\n\n"
    "اشترك في القنوات المطلوبة ثم اضغط زر التحقق بالأسفل.</blockquote>"
)

ACCOUNT_FORCE_SUB_TEXT = (
    "<blockquote><tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> "
    "<b>لإكمال المحادثة</b>\n\nاشترك أولاً في القنوات التالية ثم أرسل رسالتك مرة أخرى.</blockquote>"
 )

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def try_calculate(text):
    if not text:
        return None
    t = text.strip()
    if not re.fullmatch(r"[\d\s\.\+\-\*/\(\)×÷]+", t):
        return None
    t = t.replace("×", "*").replace("÷", "/")
    if not re.search(r"[\+\-\*/]", t):
        return None
    if len(re.findall(r"\d", t)) < 2:
        return None
    try:
        if "__" in t or "import" in t:
            return None
        result = eval(t, {"__builtins__": {}}, {})
        if isinstance(result, (int, float)):
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"{t.strip()} = {result}"
    except Exception:
        return None
    return None

CURRENCY_EMOJIS = {"ton": "5077829135573714360", "usd": "5879991085001871624", "egp": "6050934734752582943"}
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def parse_currency_request(value):
    value = (value or "").strip().lower().translate(ARABIC_DIGITS)
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(ton|t|تون|ت|usd|usdt|ustd|u|\$|dollar|dollars|دولار|دولر|egp|ج|جنيه|جنية|مصرى|مصري)", value)
    if m:
        amount_text, unit = m.group(1), m.group(2)
    else:
        # الصيغة العكسية: العملة ثم المبلغ (مثل: TON 50 أو USD 100). الرموز المفردة غير مسموحة هنا لتقليل الالتباس.
        m = re.fullmatch(r"(ton|تون|usd|usdt|ustd|\$|dollar|dollars|دولار|دولر|egp|جنيه|جنية|مصرى|مصري)\s*(\d+(?:[.,]\d+)?)", value)
        if not m:
            return None
        unit, amount_text = m.group(1), m.group(2)
    amount = float(amount_text.replace(",", "."))
    currency = "ton" if unit in {"ton", "t", "تون", "ت"} else "usd" if unit in {"usd", "usdt", "ustd", "u", "$", "dollar", "dollars", "دولار", "دولر"} else "egp"
    return amount, currency

async def fetch_live_prices():
    import math
    import urllib.request

    def load(url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"{BOT_NAME}/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))

    async def try_sources(sources, label):
        errors = []
        for url, extract in sources:
            try:
                data = await asyncio.to_thread(load, url)
                value = float(extract(data))
                if not math.isfinite(value) or value <= 0:
                    raise ValueError("قيمة سعر غير صالحة")
                return value
            except Exception as exc:
                errors.append(f"{url}: {exc}")
        raise RuntimeError(f"تعذر جلب {label}: " + " | ".join(errors))

    ton_sources = [
        (
            "https://tonapi.io/v2/rates?tokens=ton&currencies=usd",
            lambda data: data["rates"]["TON"]["prices"]["USD"],
        ),
        (
            "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd",
            lambda data: data["the-open-network"]["usd"],
        ),
    ]
    fx_sources = [
        (
            "https://open.er-api.com/v6/latest/USD",
            lambda data: data["rates"]["EGP"] if data.get("result") != "error" else None,
        ),
        (
            "https://api.exchangerate-api.com/v4/latest/USD",
            lambda data: data["rates"]["EGP"],
        ),
    ]
    try:
        ton_usd, usd_egp = await asyncio.gather(
            try_sources(ton_sources, "سعر TON بالدولار"),
            try_sources(fx_sources, "سعر الدولار بالجنيه"),
        )
        return {
            "ton_usd": ton_usd,
            "usd_egp": usd_egp,
            "ton_egp": ton_usd * usd_egp,
        }
    except Exception:
        logger.exception("Failed to fetch live currency prices")
        return None

def fmt_price(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")

def currency_prices_text(amount, currency, prices):
    if currency == "ton":
        return {
            "ton": amount,
            "usd": amount * prices["ton_usd"],
            "egp": amount * prices["ton_egp"],
        }
    if currency == "usd":
        return {
            "ton": amount / prices["ton_usd"],
            "usd": amount,
            "egp": amount * prices["usd_egp"],
        }
    return {
        "ton": amount / prices["ton_egp"],
        "usd": amount / prices["usd_egp"],
        "egp": amount,
    }

def fmt_currency_value(key, value):
    decimals = {"usd": 1, "ton": 2, "egp": 2}.get(key, 2)
    return f"{value:,.{decimals}f}".rstrip("0").rstrip(".")

def currency_keyboard(values, requested):
    labels = {"ton": "TON", "usd": "USD", "egp": "EGP"}
    styles = {"ton": "primary", "usd": "primary", "egp": "primary"}
    order = [requested] + [x for x in ("ton", "usd", "egp") if x != requested]
    rows = []
    for key in order:
        shown = fmt_currency_value(key, values[key])
        rows.append([InlineKeyboardButton(
            text=f"{labels[key]}: {shown} {labels[key]}",
            copy_text=CopyTextButton(text=f"{shown} {labels[key]}"),
            style=styles[key]
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def currency_header(amount, currency):
    labels = {"ton": "Ton", "usd": "USD", "egp": "EGP"}
    return f"<blockquote><b>• 𝖢𝗎𝗋𝗋𝖾𝗇𝗍 𝗉𝗋𝗂𝖼𝖾 𝗈𝖿  : {fmt_price(amount)} {labels[currency]}</b></blockquote>"

def currency_tool_kb(enabled):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} الرد على أسعار العملات", callback_data="currency_toggle", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="عرض الأسعار الآن", callback_data="currency_show", style="primary", icon_custom_emoji_id="5902206159095339799")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

SECTION_EMOJI_IDS = {
    "💳": "5199662703332836840",
    "💬": "6050674936475818773",
    "🚫": "6039522349517115015",
    "🔇": "6206110936789423908",
    "👋": "5985478698722136468",
    "📝": "5904219717073114606",
    "⚙️": "5877260593903177342",
}

def custom_emoji(emoji, emoji_id=None):
    emoji_id = emoji_id or SECTION_EMOJI_IDS.get(emoji) or BOT_INFO_EMOJI
    return f"<tg-emoji emoji-id='{emoji_id}'>{emoji}</tg-emoji>"

def section_message(title, emoji, *lines):
    title_block=f"<blockquote><b>{custom_emoji(emoji)} {title}</b></blockquote>"
    body="\n\n".join(f"<blockquote><b>{line}</b></blockquote>" for line in lines if line)
    return title_block + ("\n\n" + body if body else "")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def main_kb(is_admin_user=False, is_owner=False):
    rows = [
        [InlineKeyboardButton(text="اشتراك الإجباري", callback_data="account_force", style="primary", icon_custom_emoji_id="5260268501515377807"), InlineKeyboardButton(text="التفعيل والتعطيل", callback_data="toggle", style="primary", icon_custom_emoji_id="5258476306152038031")],
        [InlineKeyboardButton(text="إدارة المكتومين", callback_data="muted", style="primary", icon_custom_emoji_id="5258318620722733379"), InlineKeyboardButton(text="الكلمات الممنوعة", callback_data="words", style="primary", icon_custom_emoji_id="5260342697075416641")],
        [InlineKeyboardButton(text="الرسائل المجدولة", callback_data="scheduled", style="primary", icon_custom_emoji_id="5967412305338568701"), InlineKeyboardButton(text="طرق الدفع", callback_data="payment_home", style="primary", icon_custom_emoji_id="5258204546391351475")],
        [InlineKeyboardButton(text="إدارة الردود", callback_data="replies", style="primary", icon_custom_emoji_id="5258093637450866522"), InlineKeyboardButton(text="الإذاعة للعملاء", callback_data="broadcast", style="primary", icon_custom_emoji_id="5445180664812968189")],
        [InlineKeyboardButton(text="الشرح", callback_data="help_home", style="primary", icon_custom_emoji_id="5767288287001580715"), InlineKeyboardButton(text="الإعدادات المتقدمة", callback_data="advanced", style="primary", icon_custom_emoji_id="5904258298764334001")],
    ]
    if is_owner:
        rows.append([InlineKeyboardButton(text="إدارة الأدمنية", callback_data="admin_panel", style="primary", icon_custom_emoji_id="5789452774970236366")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

ADVANCED_BACK_ICON = "5445365692004071819"

def advanced_kb():
    rows = [
        [InlineKeyboardButton(text="إدارة رسالة الترحيب", callback_data="welcome", style="primary", icon_custom_emoji_id="5985478698722136468"), InlineKeyboardButton(text="رصد الحذف والتعديل", callback_data="tracking", style="primary", icon_custom_emoji_id="5904219717073114606")],
        [InlineKeyboardButton(text="الساعة الحية", callback_data="live_clock", style="primary", icon_custom_emoji_id="5850317551090800862"), InlineKeyboardButton(text="إدارة السوشيال ميديا", callback_data="social_media", style="primary", icon_custom_emoji_id="5447602197439218445")],
        [InlineKeyboardButton(text="إدارة الميديا", callback_data="media_manager", style="primary", icon_custom_emoji_id="5445059250382469069"), InlineKeyboardButton(text="أسعار العملات", callback_data="currency_tool", style="primary", icon_custom_emoji_id="5902206159095339799")],
        [InlineKeyboardButton(text="أكواد التحويل", callback_data="transfer_tool", style="primary", icon_custom_emoji_id="5444860552310457690"), InlineKeyboardButton(text="الآلة الحاسبة", callback_data="calculator_tool", style="primary", icon_custom_emoji_id="5935938364086685805")],
        [InlineKeyboardButton(text="تخصيص أشكال الرسائل", callback_data="account_messages", style="primary", icon_custom_emoji_id="5985478698722136468")],
        [InlineKeyboardButton(text="رجوع للوحة التحكم", callback_data="home", style="danger", icon_custom_emoji_id=ADVANCED_BACK_ICON)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def advanced_text():
    return section_message("مرحبا بك في الإعدادات المتقدمة", "⚙️", "إدارة إعدادات حسابك الخاصة بك تتم من هنا:")

def toggle_kb(enabled):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="تعطيل" if enabled else "تفعيل",
            callback_data="toggle_switch",
            style="danger" if enabled else "success",
            icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133"
        )],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def back_kb(callback_data="home"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="رجوع", callback_data=callback_data, style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def cancel_kb(target="home"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إلغاء", callback_data=target, style="danger", icon_custom_emoji_id="5447647474984449520")]
    ])

def confirm_kb(action, item_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نعم، تأكيد", callback_data=f"confirm_{action}_{item_id}", style="success", icon_custom_emoji_id="6206479140040743133")],
        [InlineKeyboardButton(text="إلغاء", callback_data="home", style="danger", icon_custom_emoji_id="5447647474984449520")]
    ])

def replies_kb(enabled=True):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} قسم الردود التلقائية", callback_data="section_toggle_replies", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="حذف رد", callback_data="reply_del_list", style="danger", icon_custom_emoji_id="6039522349517115015"), InlineKeyboardButton(text="إضافة رد جديد", callback_data="reply_add", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="عرض الردود", callback_data="reply_list", style="primary", icon_custom_emoji_id="6037397706505195857"), InlineKeyboardButton(text="تعديل رد", callback_data="reply_edit_list", style="primary", icon_custom_emoji_id="5904219717073114606")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def reply_ask_btn_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نعم، إضافة أزرار", callback_data="reply_yes_btn", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="لا، حفظ الرد", callback_data="reply_no_btn", style="primary", icon_custom_emoji_id="6030445631921721471")]
    ])

def reply_btn_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="زر نص", callback_data="btn_type_text", style="primary", icon_custom_emoji_id="5445128296276718145")],
        [InlineKeyboardButton(text="زر رابط", callback_data="btn_type_url", style="primary", icon_custom_emoji_id="5778455936410588193")],
        [InlineKeyboardButton(text="زر نسخ", callback_data="btn_type_copy", style="primary", icon_custom_emoji_id="5467397594332275071")],
        [InlineKeyboardButton(text="إلغاء", callback_data="home", style="danger", icon_custom_emoji_id="5447647474984449520")]
    ])

def reply_btn_color_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="أحمر", callback_data="btn_color_danger", style="danger", icon_custom_emoji_id="5936035511951958098")],
        [InlineKeyboardButton(text="أخضر", callback_data="btn_color_success", style="success", icon_custom_emoji_id="5935967441015282912")],
        [InlineKeyboardButton(text="أزرق", callback_data="btn_color_primary", style="primary", icon_custom_emoji_id="5936274131744988204")],
        [InlineKeyboardButton(text="إلغاء", callback_data="home", style="danger", icon_custom_emoji_id="5447647474984449520")]
    ])

def welcome_button_color_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="أحمر", callback_data="welcome_btn_color_danger", style="danger", icon_custom_emoji_id="5936035511951958098")],
        [InlineKeyboardButton(text="أخضر", callback_data="welcome_btn_color_success", style="success", icon_custom_emoji_id="5935967441015282912")],
        [InlineKeyboardButton(text="أزرق", callback_data="welcome_btn_color_primary", style="primary", icon_custom_emoji_id="5936274131744988204")],
    ])

def welcome_button_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="زر نص", callback_data="welcome_btn_type_text", style="primary")],
        [InlineKeyboardButton(text="زر رابط", callback_data="welcome_btn_type_url", style="primary")],
        [InlineKeyboardButton(text="زر نسخ", callback_data="welcome_btn_type_copy", style="primary")],
        [InlineKeyboardButton(text="إلغاء", callback_data="welcome_buttons_manage", style="danger")],
    ])

def welcome_buttons_kb(buttons, owner_id):
    rows=[]
    for i, b in enumerate(buttons):
        base={"text": b.get("label") or "زر", "style": BTN_STYLE_MAP.get(b.get("color", "primary"), "primary")}
        if b.get("icon_custom_emoji_id"):
            base["icon_custom_emoji_id"] = b["icon_custom_emoji_id"]
        if b.get("type") == "url":
            base["url"] = b.get("value", "")
        elif b.get("type") == "copy":
            base["copy_text"] = CopyTextButton(text=b.get("value", ""))
        else:
            base["callback_data"] = f"wbtn_{owner_id}_{i}"
        rows.append(InlineKeyboardButton(**base))
    packed=_rows_for_welcome(buttons, rows)
    return InlineKeyboardMarkup(inline_keyboard=packed) if packed else None

def reply_more_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إضافة زر آخر", callback_data="reply_add_more_btn", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="إدارة الأزرار والمعاينة", callback_data="bted_open_replydraft_0", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text="حفظ الرد", callback_data="reply_save_btn", style="primary", icon_custom_emoji_id="5963087934696459905")]
    ])

def reply_edit_kb(rid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تعديل الكلمة المفتاحية", callback_data=f"redit_trigger_{rid}", style="primary", icon_custom_emoji_id="5888880224195581055")],
        [InlineKeyboardButton(text="تعديل نص الرد", callback_data=f"redit_response_{rid}", style="primary", icon_custom_emoji_id="6039587087559168309")],
        [InlineKeyboardButton(text="تعديل ألوان الأزرار", callback_data=f"redit_btncolors_{rid}", style="primary", icon_custom_emoji_id="5936274131744988204")],
        [InlineKeyboardButton(text="إدارة الأزرار (تعديل/حذف/ترتيب/معاينة)", callback_data=f"bted_open_reply_{rid}", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="حذف كل الأزرار", callback_data=f"redit_clearbtns_{rid}", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="رجوع", callback_data="reply_edit_list", style="danger", icon_custom_emoji_id="5447647474984449520")]
    ])

def words_kb(enabled=True):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} قسم الكلمات الممنوعة", callback_data="section_toggle_words", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="حذف كلمة", callback_data="word_del_list", style="danger", icon_custom_emoji_id="5258130763148172425"), InlineKeyboardButton(text="إضافة كلمة", callback_data="word_add", style="primary", icon_custom_emoji_id="5258362429389152256")],
        [InlineKeyboardButton(text="عرض الكلمات", callback_data="word_list", style="primary", icon_custom_emoji_id="5258043150110301407"), InlineKeyboardButton(text="تعديل كلمة", callback_data="word_edit_list", style="primary", icon_custom_emoji_id="5257991477358763590")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def muted_kb(enabled=True):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} قسم المكتومين", callback_data="section_toggle_muted", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="كتم عميل", callback_data="mute_add", style="danger", icon_custom_emoji_id="6039522349517115015"), InlineKeyboardButton(text="رفع كتم", callback_data="mute_unmute_list", style="success", icon_custom_emoji_id="5444988177263654261")],
        [InlineKeyboardButton(text="عرض المكتومين", callback_data="mute_list", style="primary", icon_custom_emoji_id="5445255929819854310")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def force_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إضافة قناة", callback_data="force_add", style="primary", icon_custom_emoji_id="5258108352008823107")],
        [InlineKeyboardButton(text="عرض القنوات", callback_data="force_list", style="primary", icon_custom_emoji_id="5260687681733533075")],
        [InlineKeyboardButton(text="تعديل قناة", callback_data="force_edit_list", style="primary", icon_custom_emoji_id="5888620056551625531")],
        [InlineKeyboardButton(text="حذف قناة", callback_data="force_del_list", style="danger", icon_custom_emoji_id="6039522349515015")],
        [InlineKeyboardButton(text="رجوع", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def force_edit_kb(fid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تعديل المعرف", callback_data=f"fedit_channel_{fid}", style="primary", icon_custom_emoji_id="5888620056551625531")],
        [InlineKeyboardButton(text="تعديل العنوان", callback_data=f"fedit_title_{fid}", style="primary", icon_custom_emoji_id="5447389837076231920")],
        [InlineKeyboardButton(text="رجوع", callback_data="force_edit_list", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def welcome_kb(enabled=True, mode="always"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} رسالة الترحيب", callback_data="welcome_toggle", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="تغيير رسالة الترحيب", callback_data="welcome_set", style="primary", icon_custom_emoji_id="6039614175917903752"), InlineKeyboardButton(text="إعدادات رسالة الترحيب", callback_data="welcome_settings", style="primary", icon_custom_emoji_id="5447389837076231920")],
        [InlineKeyboardButton(text=f"الحالة: {'عند عدم الاتصال فقط' if mode == 'offline' else 'دائماً'}", callback_data="welcome_mode", style="primary", icon_custom_emoji_id="5116590266232341370" if mode == "offline" else "5445279663809130789")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def welcome_settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تغيير الترحيب", callback_data="welcome_set", style="primary", icon_custom_emoji_id="6039614175917903752")],
        [InlineKeyboardButton(text="إدارة أزرار الترحيب", callback_data="welcome_buttons_manage", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="إضافة/تغيير الملصق", callback_data="welcome_sticker", style="primary", icon_custom_emoji_id="6039420807900303010"), InlineKeyboardButton(text="حذف الملصق", callback_data="welcome_sticker_delete", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="حذف صورة الترحيب", callback_data="welcome_image_delete", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="معاينة الترحيب", callback_data="welcome_preview", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text="رجوع", callback_data="welcome", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def broadcast_kb(enabled=True):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} قسم الإذاعة", callback_data="section_toggle_broadcast", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="إرسال رسالة للعملاء", callback_data="broadcast_send", style="primary", icon_custom_emoji_id="6032653721853234759")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def tracking_kb(deleted=True, edited=True):
    check="6206479140040743133"; off="6206110936789423908"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if edited else 'تفعيل'} رصد التعديل", callback_data="tracking_toggle_edited", style="danger" if edited else "success", icon_custom_emoji_id=off if edited else check), InlineKeyboardButton(text=f"{'تعطيل' if deleted else 'تفعيل'} رصد الحذف", callback_data="tracking_toggle_deleted", style="danger" if deleted else "success", icon_custom_emoji_id=off if deleted else check)],
        [InlineKeyboardButton(text="عرض المعدلة", callback_data="tracking_edited", style="primary", icon_custom_emoji_id="6039420807900303010"), InlineKeyboardButton(text="عرض المحذوفة", callback_data="tracking_deleted", style="primary", icon_custom_emoji_id="5445283164207479914")],
        [InlineKeyboardButton(text="مسح السجل", callback_data="tracking_clear", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

def admin_panel_kb():
    buttons = [
        ("قسم الاشتراكات", "admin_subscription_section", "primary", "5260268501515377807"),
        ("قسم الاشتراك الإجباري", "admin_force_section", "primary", "5260268501515377807"),
        ("قسم المستخدمين والحظر", "admin_users_section", "danger", "6039522349515015"),
        ("قسم النسخ الاحتياطية", "admin_backup_section", "success", "6206479140040743133"),
        ("قسم الإذاعة", "admin_broadcast_section", "primary", "6032653721853234759"),
        ("قسم إعدادات البوت", "admin_settings_section", "primary", "6039348811363520645"),
        ("الزوز ستيشن", "elzoz", "danger", "6039522349515015"),
        ("رجوع", "home", "danger", "5445365692004071819"),
    ]
    rows = []
    for i in range(0, len(buttons), 2):
        rows.append([InlineKeyboardButton(text=t, callback_data=c, style=s, icon_custom_emoji_id=e)
                     for t, c, s, e in buttons[i:i + 2]])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def is_bot_user_blocked(user_id: int) -> bool:
    conn = await db()
    row = await fetchone(conn, "SELECT blocked FROM bot_users WHERE user_id=?", (user_id,))
    await conn.close()
    return bool(row and row["blocked"])

async def show_main(call):
    is_admin_user = await is_admin(call.from_user.id)
    is_owner = call.from_user.id == OWNER_ID
    mode = await get_setting("bot_access_mode") or "free"
    account_status = "مجاني بالكامل"
    remaining = "غير محدودة"
    if call.from_user.id != OWNER_ID:
        conn = await db(); row = await fetchone(conn, "SELECT expires_at, trial FROM bot_subscriptions WHERE user_id=?", (call.from_user.id,)); await conn.close()
        if row:
            try:
                expires = datetime.fromisoformat(row["expires_at"]); delta = expires - datetime.now(timezone.utc)
                if delta.total_seconds() > 0:
                    account_status = "نسخة تجريبية" if row["trial"] else "نسخة مدفوعة"
                    remaining = format_remaining(delta)
                else:
                    account_status = "لا يوجد اشتراك فعال"; remaining = "منتهية"
            except Exception:
                account_status = "لا يوجد اشتراك فعال"; remaining = "غير متاحة"
        else:
            if mode == "paid":
                account_status = "لا يوجد اشتراك فعال"; remaining = "غير متاحة"
    text = (
        "<blockquote><b><tg-emoji emoji-id='5985478698722136468'>👋</tg-emoji> مرحبًا بك في لوحة التحكم</b>\n\n"
        f"<tg-emoji emoji-id='5769406891289481208'>💎</tg-emoji> <b>حالة الحساب: {account_status}</b>\n"
        f"<tg-emoji emoji-id='5850317551090800862'>⏰</tg-emoji> <b>المدة المتبقية: {remaining}</b></blockquote>"
    )
    try:
        await call.message.edit_text(text, reply_markup=main_kb(is_admin_user, is_owner), parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=main_kb(is_admin_user, is_owner), parse_mode="HTML")

def format_remaining(delta):
    total = max(0, int(delta.total_seconds())); days, rem = divmod(total, 86400); hours, rem = divmod(rem, 3600); minutes = rem // 60
    parts=[]
    if days: parts.append(f"{days} يوم")
    if hours: parts.append(f"{hours} ساعة")
    if minutes and not days: parts.append(f"{minutes} دقيقة")
    return " و ".join(parts) or "أقل من دقيقة"

def parse_subscription_duration(value):
    raw=(value or "").strip().lower()
    raw=raw.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    if raw.isdigit():
        days=int(raw)
        return (timedelta(days=days), f"{days} يوم") if days > 0 else None
    import re as _re
    m=_re.fullmatch(r"(\d+)\s*([hwdm])", raw)
    if not m: return None
    n=int(m.group(1)); unit=m.group(2)
    if n <= 0: return None
    labels={"h":("ساعة",timedelta(hours=n)), "w":("أسبوع",timedelta(weeks=n)), "d":("يوم",timedelta(days=n)), "m":("شهر",timedelta(days=30*n))}
    label, span=labels[unit]
    return span, f"{n} {label}"

def subscription_notice(duration_label, expires, trial=False):
    title = "تم تفعيل النسخة التجريبية تلقائيًا لك" if trial else "تم تفعيل النسخة المدفوعة في البوت لك"
    return (f"<blockquote><b><tg-emoji emoji-id='6206378324273403309'>🎉</tg-emoji> {title}</b>\n\n"
            f"<tg-emoji emoji-id='5408910404732595664'>🕐</tg-emoji> <b>المدة : {safe_html(duration_label)}</b>\n\n"
            f"<tg-emoji emoji-id='5235895962269935073'>📅</tg-emoji> <b>تاريخ الانتهاء : {safe_html(expires.strftime('%Y-%m-%d %H:%M'))}</b></blockquote>")

async def show_public_home(target):
    display_name = safe_html(getattr(target.from_user, "first_name", "صديقي") or "صديقي")
    text = (
        f"<b><tg-emoji emoji-id='6041921818896372382'>👋</tg-emoji> أهلاً بك يا {display_name} في نظام الإدارة المتقدم.</b>\n\n"
        "<blockquote><tg-emoji emoji-id='6032994772321309200'>👤</tg-emoji> أنا مساعدك الشخصي لتأمين وحماية حسابك وإدارة ردودك باحترافية تامة.</blockquote>"
    )
    image_id = await get_setting("bot_welcome_image_file_id")
    if image_id:
        await target.answer_photo(image_id, caption=text, reply_markup=public_kb(getattr(target.from_user, "id", None)), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=public_kb(getattr(target.from_user, "id", None)), parse_mode="HTML")

async def paid_access_allowed(user_id):
    if user_id == OWNER_ID or (await get_setting("bot_access_mode") or "free") != "paid": return True
    conn=await db(); row=await fetchone(conn, "SELECT expires_at FROM bot_subscriptions WHERE user_id=?", (user_id,)); await conn.close()
    if not row: return False
    try: return datetime.fromisoformat(row["expires_at"]) > datetime.now(timezone.utc)
    except Exception: return False

async def activate_first_trial(user_id):
    if user_id == OWNER_ID or (await get_setting("bot_access_mode") or "free") != "paid":
        return None
    raw_hours = await get_setting("bot_trial_hours")
    try:
        hours = max(1, int(raw_hours or 24))
    except (TypeError, ValueError):
        hours = 24
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=hours)
    conn = await db()
    cursor = await conn.execute(
        "INSERT OR IGNORE INTO bot_subscriptions(user_id, expires_at, trial, created_at) VALUES(?, ?, 1, ?)",
        (user_id, expires.isoformat(), now.isoformat()),
    )
    await conn.commit()
    await conn.close()
    return (hours, expires) if cursor.rowcount == 1 else None

async def send_paid_gate(target):
    await _paid_gate_send(target)

# ───────── لوحة العميل: «إدارة البوت» من داخل شات العميل في Telegram Business ─────────
from aiogram.types import ReplyKeyboardRemove as _CPReplyKeyboardRemove
from aiogram.exceptions import TelegramRetryAfter as _CPRetryAfter

CPN_REPEAT_MAX = 20
CPN_REPEAT_CANCEL_TEXT = "إلغاء التكرار"
_CPN_INTERVALS = {"0": ("فوري", 0.5), "2": ("ثانيتين", 2.0), "5": ("5 ثواني", 5.0)}
_CPN_KIND_LABELS = {
    "text": "نص", "photo": "صورة", "video": "فيديو", "animation": "صورة متحركة", "sticker": "ملصق",
    "voice": "بصمة صوتية", "audio": "ملف صوتي", "document": "ملف", "video_note": "فيديو دائري",
}
_CPN_REPEAT_JOBS = {}
_CPN_VIP_READY = False


class CustomerRepeatSG(StatesGroup):
    content = State()
    count = State()
    interval = State()
    confirm = State()


async def _cpn_vip_ready():
    global _CPN_VIP_READY
    if _CPN_VIP_READY:
        return
    conn = await db()
    try:
        await conn.execute("CREATE TABLE IF NOT EXISTS vip_customers(connection_id TEXT, chat_id INTEGER, PRIMARY KEY(connection_id, chat_id))")
        await conn.commit()
    finally:
        await conn.close()
    _CPN_VIP_READY = True


async def is_vip_customer_chat(connection_id, chat_id):
    try:
        await _cpn_vip_ready()
        conn = await db()
        try:
            row = await fetchone(conn, "SELECT 1 FROM vip_customers WHERE connection_id=? AND chat_id=?", (connection_id, chat_id))
        finally:
            await conn.close()
        return bool(row)
    except Exception:
        logger.warning("VIP lookup failed", exc_info=True)
        return False


async def _cpn_set_vip(connection_id, chat_id, enabled):
    await _cpn_vip_ready()
    conn = await db()
    try:
        if enabled:
            await conn.execute("INSERT OR IGNORE INTO vip_customers(connection_id, chat_id) VALUES(?, ?)", (connection_id, chat_id))
        else:
            await conn.execute("DELETE FROM vip_customers WHERE connection_id=? AND chat_id=?", (connection_id, chat_id))
        await conn.commit()
    finally:
        await conn.close()


async def _cpn_is_muted(connection_id, chat_id):
    conn = await db()
    try:
        row = await fetchone(conn, "SELECT 1 FROM muted WHERE connection_id=? AND chat_id=?", (connection_id, chat_id))
    finally:
        await conn.close()
    return bool(row)


async def _cpn_customer(owner_id, chat_id):
    conn = await db()
    try:
        return await fetchone(
            conn,
            "SELECT c.connection_id, c.first_name, c.username, c.last_seen FROM customers c "
            "JOIN business b ON b.connection_id=c.connection_id "
            "WHERE b.user_id=? AND b.enabled=1 AND c.chat_id=? ORDER BY c.last_seen DESC LIMIT 1",
            (owner_id, chat_id),
        )
    finally:
        await conn.close()


def _cpn_ago(iso_value):
    try:
        dt = datetime.fromisoformat(iso_value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        secs = int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return "غير معروف"
    if secs < 60:
        return "الآن"

    def unit(n, one, two, few, many):
        if n == 1:
            return one
        if n == 2:
            return two
        if n <= 10:
            return f"{n} {few}"
        return f"{n} {many}"

    minutes = secs // 60
    if minutes < 60:
        return "من " + unit(minutes, "دقيقة", "دقيقتين", "دقائق", "دقيقة")
    hours = minutes // 60
    if hours < 24:
        return "من " + unit(hours, "ساعة", "ساعتين", "ساعات", "ساعة")
    return "من " + unit(hours // 24, "يوم", "يومين", "أيام", "يومًا")


def _cpn_kb(chat_id, muted, vip):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="إلغاء كتم" if muted else "كتم", callback_data=f"cpn:m:{chat_id}", style="danger" if muted else "success"),
            InlineKeyboardButton(text="إلغاء VIP" if vip else "VIP", callback_data=f"cpn:v:{chat_id}", style="danger" if vip else "success"),
        ],
        [InlineKeyboardButton(text="تكرار", callback_data=f"cpn:r:{chat_id}", style="primary")],
    ])


async def _cpn_render(bot, owner_id, chat_id):
    cust = await _cpn_customer(owner_id, chat_id)
    if not cust:
        return None, None
    bc_id = cust["connection_id"]
    name_html, username_text, id_text = await get_profile_details(bot, chat_id, cust["first_name"] or "", cust["username"] or "")
    muted = await _cpn_is_muted(bc_id, chat_id)
    vip = await is_vip_customer_chat(bc_id, chat_id)
    status = "VIP" if vip else ("مكتوم" if muted else "عادي")
    username_html = f"<code>{username_text}</code>" if username_text.startswith("@") else username_text
    text = "\n".join([
        f"<blockquote>الاسم: <b>{name_html}</b></blockquote>",
        f"<blockquote>الايدي: <code>{id_text}</code></blockquote>",
        f"<blockquote>اليوزر: {username_html}</blockquote>",
        f"<blockquote>آخر نشاط: <b>{_cpn_ago(cust['last_seen'])}</b></blockquote>",
        f"<blockquote>الحالة: <b>{status}</b></blockquote>",
    ])
    return text, _cpn_kb(chat_id, muted, vip)


async def _cpn_refresh(call, chat_id):
    try:
        text, kb = await _cpn_render(call.bot, call.from_user.id, chat_id)
        if text:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        logger.debug("customer panel refresh skipped", exc_info=True)


async def _cpn_guard(call, chat_id):
    uid = call.from_user.id
    if not await is_account_linked(uid) or not await paid_access_allowed(uid):
        await call.answer()
        return None
    cust = await _cpn_customer(uid, chat_id)
    if not cust:
        await call.answer("لم أجد هذا العميل.", show_alert=True)
        return None
    return cust


def _cpn_chat_id_from(call):
    try:
        return int(call.data.split(":")[2])
    except Exception:
        return None


async def _cpn_start_filter(message: Message):
    if not message.from_user or not message.text:
        return False
    found = re.match(r"^/start(?:@\w+)?\s+bizChat(\d+)\s*$", message.text)
    if not found:
        return False
    uid = message.from_user.id
    if not await is_account_linked(uid) or not await paid_access_allowed(uid):
        return False
    return {"cpn_chat_id": int(found.group(1))}


async def _cpn_not_command(message: Message):
    return not (message.text and message.text.startswith("/"))


@router.message(_cpn_start_filter)
async def customer_panel_open(message: Message, state: FSMContext, cpn_chat_id: int):
    await state.clear()
    owner_id = message.from_user.id
    if cpn_chat_id == owner_id:
        await message.answer("هذا حسابك أنت. افتح اللوحة من شات أحد العملاء.")
        return
    text, kb = await _cpn_render(message.bot, owner_id, cpn_chat_id)
    if not text:
        await message.answer("لم أجد هذا العميل في عملائك. يظهر العميل هنا بعد أن يراسلك مرة واحدة على الأقل.")
        return
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("cpn:m:"))
async def cpn_toggle_mute(call: CallbackQuery):
    chat_id = _cpn_chat_id_from(call)
    if chat_id is None:
        await call.answer()
        return
    cust = await _cpn_guard(call, chat_id)
    if not cust:
        return
    bc_id = cust["connection_id"]
    if not await _cpn_is_muted(bc_id, chat_id):
        if await is_vip_customer_chat(bc_id, chat_id):
            await call.answer("هذا عميل VIP. ألغِ VIP أولًا ثم اكتمه.", show_alert=True)
            return
        if chat_id in PROTECTED_MUTE_USER_ID_SET:
            await call.answer("هذا الحساب محمي ولا يمكن كتمه.", show_alert=True)
            return
        conn = await db()
        try:
            await conn.execute("INSERT OR IGNORE INTO muted(connection_id, chat_id) VALUES(?, ?)", (bc_id, chat_id))
            await conn.commit()
        finally:
            await conn.close()
        await call.answer("تم كتم العميل.")
    else:
        conn = await db()
        try:
            await conn.execute("DELETE FROM muted WHERE connection_id=? AND chat_id=?", (bc_id, chat_id))
            await conn.commit()
        finally:
            await conn.close()
        await call.answer("تم إلغاء كتم العميل.")
    await _cpn_refresh(call, chat_id)


@router.callback_query(F.data.startswith("cpn:v:"))
async def cpn_toggle_vip(call: CallbackQuery):
    chat_id = _cpn_chat_id_from(call)
    if chat_id is None:
        await call.answer()
        return
    cust = await _cpn_guard(call, chat_id)
    if not cust:
        return
    bc_id = cust["connection_id"]
    if not await is_vip_customer_chat(bc_id, chat_id):
        if await _cpn_is_muted(bc_id, chat_id):
            await call.answer("هذا العميل مكتوم. ألغِ الكتم أولًا ثم فعّل VIP.", show_alert=True)
            return
        await _cpn_set_vip(bc_id, chat_id, True)
        await call.answer("تم تفعيل VIP للعميل.")
    else:
        await _cpn_set_vip(bc_id, chat_id, False)
        await call.answer("تم إلغاء VIP للعميل.")
    await _cpn_refresh(call, chat_id)


def _cpn_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CPN_REPEAT_CANCEL_TEXT, style="danger")]],
        resize_keyboard=True,
    )


def _cpn_running_jobs(owner_id):
    return [j for j in _CPN_REPEAT_JOBS.get(owner_id, []) if not j["done"]]


@router.message(F.text == CPN_REPEAT_CANCEL_TEXT)
async def cpn_repeat_cancel(message: Message, state: FSMContext):
    if not message.from_user or not await is_account_linked(message.from_user.id):
        return
    owner_id = message.from_user.id
    current = await state.get_state()
    if current and str(current).startswith("CustomerRepeatSG:"):
        await state.clear()
    running = _cpn_running_jobs(owner_id)
    for job in running:
        job["stop"].set()
    if not running:
        await message.answer("<blockquote><b>تم إلغاء التكرار.</b></blockquote>", reply_markup=_CPReplyKeyboardRemove(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cpn:r:"))
async def cpn_repeat_start(call: CallbackQuery, state: FSMContext):
    chat_id = _cpn_chat_id_from(call)
    if chat_id is None:
        await call.answer()
        return
    cust = await _cpn_guard(call, chat_id)
    if not cust:
        return
    owner_id = call.from_user.id
    if any(j["chat_id"] == chat_id for j in _cpn_running_jobs(owner_id)):
        await call.answer("يوجد تكرار شغال لهذا العميل. ألغِه أولًا.", show_alert=True)
        return
    conn = await db()
    try:
        biz = await fetchone(conn, "SELECT can_reply FROM business WHERE connection_id=?", (cust["connection_id"],))
    finally:
        await conn.close()
    if biz and biz["can_reply"] is not None and not biz["can_reply"]:
        await call.answer("البوت غير مسموح له بالرد في محادثات حسابك. فعّل صلاحية الرد من إعدادات Business.", show_alert=True)
        return
    await state.clear()
    await state.set_state(CustomerRepeatSG.content)
    await state.update_data(cpn_chat_id=chat_id, cpn_bc=cust["connection_id"], cpn_name=safe_html(cust["first_name"] or str(chat_id)))
    await call.answer()
    await call.message.answer("أرسل الآن النص أو الميديا التي تريد تكرارها للعميل:", reply_markup=_cpn_cancel_kb())


def _cpn_extract_payload(message):
    try:
        html_value = message.html_text or ""
    except Exception:
        html_value = ""
    if message.text:
        return {"kind": "text", "text": html_value or message.text}
    caption = html_value if message.caption else ""
    if message.photo:
        return {"kind": "photo", "file_id": message.photo[-1].file_id, "caption": caption}
    if message.video:
        return {"kind": "video", "file_id": message.video.file_id, "caption": caption}
    if message.animation:
        return {"kind": "animation", "file_id": message.animation.file_id, "caption": caption}
    if message.voice:
        return {"kind": "voice", "file_id": message.voice.file_id, "caption": caption}
    if message.audio:
        return {"kind": "audio", "file_id": message.audio.file_id, "caption": caption}
    if message.document:
        return {"kind": "document", "file_id": message.document.file_id, "caption": caption}
    if message.sticker:
        return {"kind": "sticker", "file_id": message.sticker.file_id}
    if message.video_note:
        return {"kind": "video_note", "file_id": message.video_note.file_id}
    return None


@router.message(CustomerRepeatSG.content, _cpn_not_command)
async def cpn_repeat_content(message: Message, state: FSMContext):
    payload = _cpn_extract_payload(message)
    if not payload:
        await message.answer("هذا النوع غير مدعوم. أرسل نصًا أو صورة أو فيديو أو ملصقًا أو ملفًا أو بصمة صوتية.")
        return
    await state.update_data(cpn_payload=payload)
    await state.set_state(CustomerRepeatSG.count)
    await message.answer(f"كم مرة تريد تكرارها؟ اكتب رقمًا من 1 إلى {CPN_REPEAT_MAX}.")


def _cpn_interval_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=f"cpn:i:{key}", style="primary")
        for key, (label, _delay) in _CPN_INTERVALS.items()
    ]])


@router.message(CustomerRepeatSG.count, _cpn_not_command)
async def cpn_repeat_count(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not re.fullmatch(r"\d{1,3}", raw) or not (1 <= int(raw) <= CPN_REPEAT_MAX):
        await message.answer(f"اكتب رقمًا صحيحًا من 1 إلى {CPN_REPEAT_MAX}.")
        return
    await state.update_data(cpn_count=int(raw))
    await state.set_state(CustomerRepeatSG.interval)
    await message.answer("اختر الفاصل بين كل رسالة والتي بعدها:", reply_markup=_cpn_interval_kb())


def _cpn_summary(data):
    kind_label = _CPN_KIND_LABELS.get(data["cpn_payload"]["kind"], "رسالة")
    delay_label = _CPN_INTERVALS[data["cpn_interval"]][0]
    return (
        "<blockquote><b>تأكيد التكرار</b></blockquote>\n"
        f"<blockquote>العميل: <b>{data['cpn_name']}</b></blockquote>\n"
        f"<blockquote>المحتوى: <b>{kind_label}</b></blockquote>\n"
        f"<blockquote>العدد: <b>{data['cpn_count']}</b></blockquote>\n"
        f"<blockquote>الفاصل: <b>{delay_label}</b></blockquote>"
    )


@router.callback_query(F.data.startswith("cpn:i:"), CustomerRepeatSG.interval)
async def cpn_repeat_interval(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[2]
    if key not in _CPN_INTERVALS:
        await call.answer()
        return
    await state.update_data(cpn_interval=key)
    await state.set_state(CustomerRepeatSG.confirm)
    data = await state.get_data()
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="بدء التكرار", callback_data="cpn:go", style="success"),
        InlineKeyboardButton(text="إلغاء", callback_data="cpn:no", style="danger"),
    ]])
    await call.answer()
    try:
        await call.message.edit_text(_cpn_summary(data), reply_markup=confirm_kb, parse_mode="HTML")
    except Exception:
        logger.debug("repeat summary edit skipped", exc_info=True)


def _cpn_progress_text(job):
    return f"<blockquote><b>جاري التكرار للعميل: {job['name']}</b>\nتم إرسال {job['sent']} من {job['count']}</blockquote>"


async def _cpn_send_payload(bot, bc_id, chat_id, payload):
    kw = {"chat_id": chat_id, "business_connection_id": bc_id}
    kind = payload["kind"]
    caption = payload.get("caption") or None
    if kind == "text":
        await bot.send_message(text=payload["text"], parse_mode="HTML", **kw)
    elif kind == "photo":
        await bot.send_photo(photo=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "video":
        await bot.send_video(video=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "animation":
        await bot.send_animation(animation=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "voice":
        await bot.send_voice(voice=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "audio":
        await bot.send_audio(audio=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "document":
        await bot.send_document(document=payload["file_id"], caption=caption, parse_mode="HTML", **kw)
    elif kind == "sticker":
        await bot.send_sticker(sticker=payload["file_id"], **kw)
    elif kind == "video_note":
        await bot.send_video_note(video_note=payload["file_id"], **kw)
    else:
        raise ValueError("unsupported repeat content")


async def _cpn_repeat_runner(bot, job):
    owner_id = job["owner"]
    total = job["count"]
    reason = "done"
    error_text = ""
    cancelled = False
    loop = asyncio.get_running_loop()
    last_edit = loop.time()
    try:
        for index in range(total):
            if job["stop"].is_set():
                reason = "stopped"
                break
            for attempt in range(2):
                try:
                    await _cpn_send_payload(bot, job["bc"], job["chat_id"], job["payload"])
                    break
                except _CPRetryAfter as exc:
                    if attempt == 1:
                        raise
                    await asyncio.sleep(float(getattr(exc, "retry_after", 1) or 1) + 0.5)
            job["sent"] += 1
            if index + 1 >= total:
                break
            if loop.time() - last_edit >= 1.5:
                last_edit = loop.time()
                try:
                    await bot.edit_message_text(chat_id=owner_id, message_id=job["msg_id"], text=_cpn_progress_text(job), parse_mode="HTML")
                except Exception:
                    pass
            try:
                await asyncio.wait_for(job["stop"].wait(), timeout=job["delay"])
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        cancelled = True
        raise
    except Exception as exc:
        reason = "error"
        error_text = safe_html(str(exc)[:150])
        logger.exception("Customer repeat failed")
    finally:
        job["done"] = True
        jobs = _CPN_REPEAT_JOBS.get(owner_id, [])
        if job in jobs:
            jobs.remove(job)
        if not cancelled:
            try:
                if reason == "done":
                    final = f"<blockquote><b>اكتمل التكرار</b>\nتم إرسال {job['sent']} من {total} رسالة إلى {job['name']}.</blockquote>"
                elif reason == "stopped":
                    final = f"<blockquote><b>تم إيقاف التكرار</b>\nتم إرسال {job['sent']} من {total} رسالة إلى {job['name']}.</blockquote>"
                else:
                    final = f"<blockquote><b>توقف التكرار بسبب خطأ</b>\nتم إرسال {job['sent']} من {total} رسالة إلى {job['name']}.\nالسبب: {error_text}</blockquote>"
                if _cpn_running_jobs(owner_id):
                    await bot.edit_message_text(chat_id=owner_id, message_id=job["msg_id"], text=final, parse_mode="HTML")
                else:
                    try:
                        await bot.delete_message(chat_id=owner_id, message_id=job["msg_id"])
                    except Exception:
                        pass
                    await bot.send_message(chat_id=owner_id, text=final, reply_markup=_CPReplyKeyboardRemove(), parse_mode="HTML")
            except Exception:
                logger.warning("Failed to report repeat result", exc_info=True)


@router.callback_query(F.data == "cpn:go", CustomerRepeatSG.confirm)
async def cpn_repeat_go(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    chat_id = data.get("cpn_chat_id")
    payload = data.get("cpn_payload")
    count = data.get("cpn_count")
    interval_key = data.get("cpn_interval")
    if not (chat_id and payload and count and interval_key in _CPN_INTERVALS):
        await call.answer("انتهت صلاحية هذا الزر.")
        return
    cust = await _cpn_guard(call, chat_id)
    if not cust:
        return
    owner_id = call.from_user.id
    if any(j["chat_id"] == chat_id for j in _cpn_running_jobs(owner_id)):
        await call.answer("يوجد تكرار شغال لهذا العميل. ألغِه أولًا.", show_alert=True)
        return
    await call.answer("بدأ التكرار.")
    try:
        await call.message.delete()
    except Exception:
        pass
    job = {
        "owner": owner_id, "chat_id": chat_id, "bc": cust["connection_id"], "payload": payload,
        "count": count, "delay": _CPN_INTERVALS[interval_key][1], "sent": 0,
        "stop": asyncio.Event(), "done": False, "name": data.get("cpn_name") or str(chat_id), "msg_id": None,
    }
    progress = await call.bot.send_message(chat_id=owner_id, text=_cpn_progress_text(job), parse_mode="HTML")
    job["msg_id"] = progress.message_id
    _CPN_REPEAT_JOBS.setdefault(owner_id, []).append(job)
    spawn(_cpn_repeat_runner(call.bot, job))


@router.callback_query(F.data == "cpn:no")
async def cpn_repeat_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("تم إلغاء التكرار.")
    try:
        await call.message.delete()
    except Exception:
        pass
    if not _cpn_running_jobs(call.from_user.id):
        await call.bot.send_message(chat_id=call.from_user.id, text="<blockquote><b>تم إلغاء التكرار.</b></blockquote>", reply_markup=_CPReplyKeyboardRemove(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cpn:"))
async def cpn_stale(call: CallbackQuery):
    await call.answer("انتهت صلاحية هذا الزر. افتح اللوحة من جديد.")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user and message.from_user.id != OWNER_ID and await is_bot_user_blocked(message.from_user.id):
        await message.answer("تم حظرك من استخدام البوت.")
        return
    is_first_start = False
    first_trial = None
    first_start_number = None
    if message.from_user and message.from_user.id != OWNER_ID:
        conn = await db()
        cursor = await conn.execute(
            "INSERT OR IGNORE INTO bot_users(user_id, first_name, username, first_seen) VALUES(?, ?, ?, ?)",
            (
                message.from_user.id,
                message.from_user.first_name or "",
                message.from_user.username or "",
                datetime.now(timezone.utc).isoformat(),
            )
        )
        is_first_start = cursor.rowcount == 1
        if is_first_start:
            row = await fetchone(conn, "SELECT COUNT(*) AS c FROM bot_users WHERE user_id!=?", (OWNER_ID,))
            first_start_number = row["c"] if row else None
        await conn.commit()
        await conn.close()
        if is_first_start:
            first_trial = await activate_first_trial(message.from_user.id)
            await _referral_register(message)

    if message.from_user and not await paid_access_allowed(message.from_user.id):
        await send_paid_gate(message)
        return

    if is_first_start and first_start_number is not None:
        start_name = safe_html(message.from_user.full_name or message.from_user.first_name or "غير معروف")
        start_username = f"@{safe_html(message.from_user.username)}" if message.from_user.username else "غير متوفر"
        start_text = (
            "<blockquote><tg-emoji emoji-id='5985478698722136468'>👤</tg-emoji> "
            f"<b>مستخدم جديد دخل البوت رقم {first_start_number}</b>\n\n"
            f"الاسم: {start_name}\n"
            f"اليوزر: {start_username}\n"
            f"الآيدي: <code>{message.from_user.id}</code></blockquote>"
        )
        start_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="فتح بروفايل المستخدم",
                url=f"tg://user?id={message.from_user.id}",
                style="primary",
                icon_custom_emoji_id="5452085950022707790"
            )
        ]])
        try:
            await message.bot.send_message(
                chat_id=OWNER_ID,
                text=start_text,
                reply_markup=start_kb,
                parse_mode="HTML"
            )
        except Exception:
            logger.exception("Failed to send first /start notice")
    missing_bot_subs = await required_subs(message.bot, message.from_user.id, OWNER_ID, scope="bot") if (await get_setting("bot_force_enabled") or 0) else []
    if missing_bot_subs:
        await message.answer(
            await get_bot_message("bot_force_sub"),
            reply_markup=bot_sub_kb(missing_bot_subs),
            parse_mode="HTML"
        )
        return
    if first_trial:
        hours, expires = first_trial
        await message.answer(subscription_notice(f"{hours} ساعة", expires, trial=True), parse_mode="HTML")
    await show_public_home(message)

@router.callback_query(F.data == "bot_force_verify")
async def bot_force_verify(call: CallbackQuery, state: FSMContext):
    missing_bot_subs = await required_subs(call.bot, call.from_user.id, OWNER_ID, scope="bot")
    if missing_bot_subs:
        await call.message.edit_text(
            await get_bot_message("bot_force_sub"),
            reply_markup=bot_sub_kb(missing_bot_subs),
            parse_mode="HTML"
        )
        await call.answer("لم يكتمل الاشتراك في كل القنوات.", show_alert=True)
        return
    await state.clear()
    await edit_or_replace(call, "تم التحقق من الاشتراك بنجاح.", public_kb(call.from_user.id))
    await call.answer("تم التحقق بنجاح.")

@router.callback_query(F.data == "public_home")
async def public_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    display_name = safe_html(call.from_user.first_name or "صديقي")
    home_text = (
        f"<b><tg-emoji emoji-id='6041921818896372382'>👋</tg-emoji> أهلاً بك يا {display_name} في نظام الإدارة المتقدم.</b>\n\n"
        "<blockquote><tg-emoji emoji-id='6032994772321309200'>👤</tg-emoji> أنا مساعدك الشخصي لتأمين وحماية حسابك وإدارة ردودك باحترافية تامة.</blockquote>"
    )
    image_id = await get_setting("bot_welcome_image_file_id")
    try:
        await call.message.delete()
    except Exception:
        pass
    if image_id:
        await call.message.answer_photo(image_id, caption=home_text, reply_markup=public_kb(call.from_user.id), parse_mode="HTML")
    else:
        await call.message.answer(home_text, reply_markup=public_kb(call.from_user.id), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "control_panel")
async def control_panel(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    if not await paid_access_allowed(user_id):
        await send_paid_gate(call.message)
        await call.answer()
        return
    missing_bot_subs = await required_subs(bot, user_id, OWNER_ID, scope="bot") if (await get_setting("bot_force_enabled") or 0) else []
    if missing_bot_subs:
        await edit_or_replace(call, BOT_FORCE_SUB_TEXT, bot_sub_kb(missing_bot_subs))
        await call.answer("اشترك أولاً في القنوات المطلوبة.", show_alert=True)
        return
    if not await is_account_linked(user_id):
        try:
            bot_info = await bot.get_me()
            bot_username = f"@{bot_info.username}" if bot_info.username else "يوزر البوت"
        except Exception:
            bot_username = "يوزر البوت"
        link_text = (
            "<b><tg-emoji emoji-id='5769248574499983619'>🔄</tg-emoji> اربط حسابك خلال دقائق:</b>\n\n"
            "<blockquote>"
            "<tg-emoji emoji-id='5364021841801262907'>1️⃣</tg-emoji> انسخ يوزر البوت: " + safe_html(bot_username) + "\n"
            "<tg-emoji emoji-id='5363858809137677324'>2️⃣</tg-emoji> اضغط على زر 'اذهب للاعدادات' بالأسفل.\n"
            "<tg-emoji emoji-id='5363938558090425835'>3️⃣</tg-emoji> توجه إلى خيار 'المحادثة الآلية'.\n"
            "<tg-emoji emoji-id='5363839335755953463'>4️⃣</tg-emoji> الصق يوزر البوت في حقل الإضافة."
            "</blockquote>"
        )
        dashboard_video = await get_setting("dashboard_video_file_id")
        if dashboard_video:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer_video(dashboard_video, caption=link_text, reply_markup=link_help_kb(), parse_mode="HTML")
        else:
            await edit_or_replace(call, link_text, link_help_kb())
        await call.answer("اربط حسابك أولاً.", show_alert=True)
        return
    if not await is_admin(user_id):
        await edit_or_replace(call, "تم ربط الحساب بنجاح، لكن لوحة التحكم متاحة للمالك أو الأدمن فقط.", link_help_kb())
        await call.answer()
        return
    await state.clear()
    await show_main(call)
    await call.answer()

@router.callback_query(F.data == "home")
async def home(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await edit_or_replace(call, f"<tg-emoji emoji-id='6041921818896372382'>👋</tg-emoji> أهلاً بك يا {safe_html(call.from_user.first_name or 'صديقي')} في نظام الإدارة المتقدم.\n\n<blockquote><tg-emoji emoji-id='6032994772321309200'>👤</tg-emoji> أنا مساعدك الشخصي لتأمين وحماية حسابك وإدارة ردودك باحترافية تامة.</blockquote>", public_kb(call.from_user.id))
        await call.answer()
        return
    await state.clear()
    await show_main(call)
    await call.answer()

def social_kb(enabled=True):
    toggle_style = "danger" if enabled else "success"
    toggle_emoji = "6206110936789423908" if enabled else "6206479140040743133"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'إلغاء تفعيل' if enabled else 'تفعيل'} قسم السوشيال ميديا", callback_data="social_toggle", style=toggle_style, icon_custom_emoji_id=toggle_emoji)],
        [InlineKeyboardButton(text="تيك توك", callback_data="social_edit_tiktok", style="primary", icon_custom_emoji_id="5426903221031414307"), InlineKeyboardButton(text="انستقرام", callback_data="social_edit_instagram", style="primary", icon_custom_emoji_id="5429308145019136708")],
        [InlineKeyboardButton(text="تليجرام", callback_data="social_edit_telegram", style="primary", icon_custom_emoji_id="5426990524831642021"), InlineKeyboardButton(text="فيسبوك", callback_data="social_edit_facebook", style="primary", icon_custom_emoji_id="5429591007270283448")],
        [InlineKeyboardButton(text="يوتيوب", callback_data="social_edit_youtube", style="primary", icon_custom_emoji_id="5427158904729513162")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

async def render_social(call, owner_id=None):
    owner_id = owner_id or await settings_owner(call.from_user.id)
    await ensure_account_settings(owner_id)
    conn = await db()
    row = await fetchone(conn, "SELECT social_enabled, social_tiktok, social_instagram, social_telegram, social_facebook, social_youtube FROM settings WHERE owner_id=?", (owner_id,))
    await conn.close()
    vals = {k: (row[k] or "غير مضاف") for k in ("social_tiktok", "social_instagram", "social_telegram", "social_facebook", "social_youtube")}
    text = ("<tg-emoji emoji-id='5447602197439218445'>📱</tg-emoji> <b>إدارة السوشيال ميديا</b>\n\n<blockquote>" f"الحالة: <b>{'مفعّل' if row['social_enabled'] else 'معطّل'}</b>\n" f"تقدر تضيف روابط حساباتك على منصات التواصل، وهيظهر رابط المنصة للعميل عند الطلب.\n\nتيك توك: {safe_html(vals['social_tiktok'])}\nانستقرام: {safe_html(vals['social_instagram'])}\nتليجرام: {safe_html(vals['social_telegram'])}\nفيسبوك: {safe_html(vals['social_facebook'])}\nيوتيوب: {safe_html(vals['social_youtube'])}</blockquote>")
    await call.message.edit_text(text, reply_markup=social_kb(bool(row['social_enabled'])), parse_mode="HTML")

@router.callback_query(F.data == "social_media")
async def social_media(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_social(call)
    await call.answer()

@router.callback_query(F.data == "social_toggle")
async def social_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id)
    current = await get_account_setting(owner, "social_enabled") or 0
    await set_account_setting(owner, "social_enabled", 0 if current else 1)
    await render_social(call)
    await call.answer("تم تحديث الحالة")

@router.callback_query(F.data.startswith("social_edit_"))
async def social_edit(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    platform = call.data[len("social_edit_"):]
    await state.update_data(social_platform=platform, social_owner=await settings_owner(call.from_user.id))
    await state.set_state(SocialSG.value)
    await call.message.edit_text(f"أرسل رابط حساب {platform} أو اكتب <code>حذف</code>.", reply_markup=cancel_kb("advanced"), parse_mode="HTML")
    await call.answer()

def valid_social_url(platform, value):
    try:
        parsed = urlparse(value.strip())
        host = (parsed.netloc or "").lower().split(":")[0].removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or not host:
            return False
        domains = {
            "tiktok": ("tiktok.com",),
            "instagram": ("instagram.com",),
            "telegram": ("t.me", "telegram.me", "telegram.org"),
            "facebook": ("facebook.com", "fb.com"),
            "youtube": ("youtube.com", "youtu.be"),
        }
        return any(host == domain or host.endswith("." + domain) for domain in domains.get(platform, ()))
    except Exception:
        return False

@router.message(SocialSG.value)
async def social_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    data = await state.get_data(); value = (message.text or "").strip()
    value = "" if value == "حذف" else value
    platform = data.get("social_platform")
    if platform not in {"tiktok", "instagram", "telegram", "facebook", "youtube"} or not value and (message.text or "").strip() != "حذف":
        await message.answer("أرسل رابطاً صحيحاً أو اكتب حذف."); return
    if value and not valid_social_url(platform, value):
        names = {"tiktok": "تيك توك", "instagram": "انستقرام", "telegram": "تليجرام", "facebook": "فيسبوك", "youtube": "يوتيوب"}
        await message.answer(f"الرابط لا يبدو رابط {names.get(platform, platform)} صحيحاً. أرسل رابط المنصة نفسها أو اكتب حذف.")
        return
    await set_account_setting(data.get("social_owner"), f"social_{platform}", value)
    await state.clear(); await message.answer("تم حفظ حساب السوشيال ميديا.", reply_markup=back_kb("social_media"), parse_mode="HTML")


def payment_menu_keyboard(keys, group=False):
    rows = []
    buttons = []
    for key in keys:
        if key == "egypt_group":
            info = PAYMENT_GROUP
            callback = "payment_egypt"
        else:
            info = PAYMENT_METHODS[key]
            callback = f"payment_wallet_{key}"
        buttons.append(InlineKeyboardButton(
            text=info["name"], callback_data=callback, style="primary",
            icon_custom_emoji_id=info["emoji"],
        ))
    rows.extend([buttons[i:i + 2] for i in range(0, len(buttons), 2)])
    back_callback = "payment_home" if group else "home"
    rows.append([InlineKeyboardButton(text="رجوع", callback_data=back_callback, style="danger", icon_custom_emoji_id="5445365692004071819")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_section_keyboard(keys, enabled=True):
    base=payment_menu_keyboard(keys)
    base.inline_keyboard.insert(0, [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} قسم طرق الدفع", callback_data="section_toggle_payment", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")])
    return base

def payment_manage_keyboard(key, enabled):
    info = PAYMENT_METHODS[key]
    back_callback = "payment_egypt" if key in PAYMENT_EGYPT_ORDER else "payment_home"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"حالة الرد التلقائي: {'مفعل' if enabled else 'معطل'}",
                callback_data=f"payment_toggle_{key}",
                style="success" if enabled else "danger",
                icon_custom_emoji_id="6206479140040743133" if enabled else "6206110936789423908",
            ),
            InlineKeyboardButton(
                text="تعديل البيانات", callback_data=f"payment_edit_{key}",
                style="primary", icon_custom_emoji_id="6050674936475818773",
            ),
        ],
        [InlineKeyboardButton(text="رجوع", callback_data=back_callback, style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])


async def get_payment_wallet(owner_id, key):
    conn = await db()
    row = await fetchone(conn, "SELECT wallet_value, network, enabled FROM payment_wallets WHERE owner_id=? AND wallet_key=?", (owner_id, key))
    await conn.close()
    return row


async def save_payment_wallet(owner_id, key, value, network=""):
    conn = await db()
    await conn.execute(
        "INSERT INTO payment_wallets(owner_id, wallet_key, wallet_value, network, enabled, updated_at) VALUES(?, ?, ?, ?, 1, ?) "
        "ON CONFLICT(owner_id, wallet_key) DO UPDATE SET wallet_value=excluded.wallet_value, network=excluded.network, updated_at=excluded.updated_at",
        (owner_id, key, value, network, datetime.now(timezone.utc).isoformat()),
    )
    await conn.commit()
    await conn.close()


async def toggle_payment_wallet(owner_id, key):
    row = await get_payment_wallet(owner_id, key)
    enabled = 0 if (int(row["enabled"]) if row else 1) else 1
    conn = await db()
    await conn.execute(
        "INSERT INTO payment_wallets(owner_id, wallet_key, enabled, updated_at) VALUES(?, ?, ?, ?) "
        "ON CONFLICT(owner_id, wallet_key) DO UPDATE SET enabled=excluded.enabled, updated_at=excluded.updated_at",
        (owner_id, key, enabled, datetime.now(timezone.utc).isoformat()),
    )
    await conn.commit()
    await conn.close()
    return bool(enabled)


async def payment_wallet_panel(owner_id, key):
    row = await get_payment_wallet(owner_id, key)
    info = PAYMENT_METHODS[key]
    name = safe_html(info["name"])
    icon = f"<tg-emoji emoji-id='{info['emoji']}'>{info['fallback']}</tg-emoji>"
    value = safe_html(row["wallet_value"] if row else "")
    network = safe_html(row["network"] if row else "")
    enabled = bool(row["enabled"]) if row else True
    lines = [
        f"<blockquote><b>╕═══ {icon} المحفظة {name} ══╒</b></blockquote>",
        "<blockquote><b><tg-emoji emoji-id='5447389837076231920'>📌</tg-emoji> العنوان/القيمة الحالية:</b></blockquote>",
    ]
    if network:
        lines.append(f"<blockquote><b>الشبكة: <code>{network}</code></b></blockquote>")
    lines.append(f"<blockquote><b>{f'<code>{value}</code>' if value else 'لم يتم التعيين بعد'}</b></blockquote>")
    if value:
        lines.append(f"<blockquote><b>نوع البيانات تلقائيًا: {payment_data_type_label(classify_payment_value(row['wallet_value'], key))}</b></blockquote>")
    lines.extend([
        "<blockquote><b>اختر من الأسفل لتعديل أو تعطيل هذه المحفظة فقط:</b></blockquote>",
        "<blockquote><b>╘═════════════════════════╛</b></blockquote>",
    ])
    return "\n".join(lines), payment_manage_keyboard(key, enabled)


def classify_payment_value(value, wallet_key=None):
    raw = (value or "").strip()
    digit_map = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    normalized = raw.translate(digit_map)
    compact_phone = re.sub(r"[\s().-]", "", normalized)
    if re.fullmatch(r"\+?\d{7,15}", compact_phone):
        if compact_phone.startswith(("+", "00")) or (compact_phone.startswith("0") and len(compact_phone.lstrip("+")) >= 10):
            return "phone"

    lowered = normalized.casefold()
    if "@" in lowered or "http://" in lowered or "https://" in lowered or lowered.startswith("www."):
        return "address"
    if re.fullmatch(r"0x[a-f0-9]{20,}", normalized, flags=re.IGNORECASE):
        return "address"
    if re.fullmatch(r"(?:EQ|UQ)[A-Za-z0-9_-]{30,}", normalized):
        return "address"
    if re.fullmatch(r"T[A-Za-z0-9]{30,}", normalized):
        return "address"
    if re.fullmatch(r"bc1[a-z0-9]{20,}", normalized, flags=re.IGNORECASE):
        return "address"
    if len(normalized) >= 25 and re.fullmatch(r"[A-Za-z0-9_-]+", normalized) and re.search(r"[A-Za-z]", normalized) and re.search(r"[0-9]", normalized):
        return "address"
    return "id"


def payment_data_type_label(kind):
    return {"phone": "رقم الهاتف", "address": "العنوان", "id": "ID"}.get(kind, "ID")


def payment_customer_text(key, wallet):
    info = PAYMENT_METHODS[key]
    name = safe_html(PAYMENT_CUSTOMER_NAMES.get(key, info["name"]))
    icon = f"<tg-emoji emoji-id='{info['emoji']}'>{info['fallback']}</tg-emoji>"
    raw_value = wallet["wallet_value"] or ""
    value = safe_html(raw_value)
    data_label = payment_data_type_label(classify_payment_value(raw_value, key))
    network = safe_html(wallet["network"] or "")
    separator = "━━━━━━━━━━━━━━━━━━━━"
    sections = [
        f"<blockquote><b>{name} {icon}</b></blockquote>",
    ]
    if network:
        sections.append(f"<blockquote><b>الشبكة: <code>{network}</code></b></blockquote>")
    sections.extend([
        f"<blockquote><b>{data_label}: <code>{value}</code> <tg-emoji emoji-id='5303068786922893194'>✨</tg-emoji></b></blockquote>",
        f"<blockquote><b>{separator}</b></blockquote>",
        "<blockquote><b>أرسل لقطة شاشة للدفع من فضلك <tg-emoji emoji-id='5300978181526798066'>👤</tg-emoji></b></blockquote>",
    ])
    return "\n".join(sections)


def payment_customer_keyboard(wallet_value):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Click to copy",
            copy_text=CopyTextButton(text=wallet_value),
            style="primary",
        )
    ]])


async def send_payment_details(message, key, wallet, business_connection_id=None):
    wallet_value = wallet["wallet_value"]
    kwargs = {
        "chat_id": message.chat.id,
        "text": payment_customer_text(key, wallet),
        "reply_markup": payment_customer_keyboard(wallet_value),
        "parse_mode": "HTML",
    }
    if business_connection_id:
        kwargs["business_connection_id"] = business_connection_id
    await message.bot.send_message(**kwargs)


@router.callback_query(F.data.startswith("bpay_"))
async def business_payment_choice(call: CallbackQuery):
    key=call.data.removeprefix("bpay_")
    bc_id=getattr(call.message, "business_connection_id", None)
    if key not in PAYMENT_METHODS or not bc_id:
        await call.answer("تعذر تحديد طريقة الدفع.", show_alert=True); return
    conn=await db(); row=await fetchone(conn, "SELECT user_id FROM business WHERE connection_id=?", (bc_id,)); await conn.close()
    if not row: await call.answer(); return
    if not call.from_user or call.from_user.id != row["user_id"]:
        await call.answer()
        return
    wallet=await get_payment_wallet(row["user_id"], key)
    if not wallet or not wallet["enabled"] or not wallet["wallet_value"]: await call.answer("الطريقة غير متاحة حالياً.", show_alert=True); return
    try:
        await call.message.delete()
    except Exception: pass
    await send_payment_details(call.message, key, wallet, business_connection_id=bc_id)
    await call.answer()

@router.callback_query(F.data == "payment_home")
async def payment_home(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه الخاصية للأدمن فقط.", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        section_message("طرق الدفع", "💳", "أضف بيانات وسائل الدفع الخاصة بك ليتم إرسالها تلقائياً عند طلب الدفع.", "اختار وسيلة الدفع التي تريد إدارتها."),
        reply_markup=payment_section_keyboard(PAYMENT_ENTRY_ORDER, bool(await get_account_setting(await settings_owner(call.from_user.id), "payment_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "payment_enabled") is not None else 1)), parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "payment_egypt")
async def payment_egypt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه الخاصية للأدمن فقط.", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        "<blockquote><b>الشبكات المصرية</b></blockquote>\nاختر الشبكة:",
        reply_markup=payment_menu_keyboard(PAYMENT_EGYPT_ORDER, group=True), parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("payment_wallet_"))
async def payment_wallet_open(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه الخاصية للأدمن فقط.", show_alert=True)
        return
    key = call.data.removeprefix("payment_wallet_")
    if key not in PAYMENT_METHODS:
        await call.answer("وسيلة الدفع غير معروفة.", show_alert=True)
        return
    await state.clear()
    owner = await settings_owner(call.from_user.id)
    text, keyboard = await payment_wallet_panel(owner, key)
    await edit_or_replace(call, text, keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("payment_toggle_"))
async def payment_wallet_toggle(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه الخاصية للأدمن فقط.", show_alert=True)
        return
    key = call.data.removeprefix("payment_toggle_")
    if key not in PAYMENT_METHODS:
        await call.answer("وسيلة الدفع غير معروفة.", show_alert=True)
        return
    owner = await settings_owner(call.from_user.id)
    await toggle_payment_wallet(owner, key)
    text, keyboard = await payment_wallet_panel(owner, key)
    await edit_or_replace(call, text, keyboard)
    await call.answer("تم تحديث حالة المحفظة.")


@router.callback_query(F.data.startswith("payment_edit_"))
async def payment_wallet_edit(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه الخاصية للأدمن فقط.", show_alert=True)
        return
    key = call.data.removeprefix("payment_edit_")
    if key not in PAYMENT_METHODS:
        await call.answer("وسيلة الدفع غير معروفة.", show_alert=True)
        return
    info = PAYMENT_METHODS[key]
    await state.clear()
    await state.update_data(payment_owner=await settings_owner(call.from_user.id), payment_key=key)
    if info.get("network_required"):
        await state.set_state(PaymentSG.network)
        prompt = info["network_prompt"]
    else:
        await state.update_data(payment_network="")
        await state.set_state(PaymentSG.value)
        prompt = info["prompt"]
    await call.message.edit_text(
        f"<tg-emoji emoji-id='6050674936475818773'>💬</tg-emoji> {safe_html(prompt)}",
        reply_markup=cancel_kb(), parse_mode="HTML",
    )
    await call.answer()


@router.message(PaymentSG.network)
async def payment_network_receive(message: Message, state: FSMContext):
    if not message.from_user or not await is_admin(message.from_user.id):
        return
    network = (message.text or "").strip()
    data = await state.get_data()
    key = data.get("payment_key")
    if key not in PAYMENT_METHODS or not PAYMENT_METHODS[key].get("network_required"):
        await state.clear()
        await message.answer("انتهت جلسة الإعداد؛ افتح طرق الدفع وحاول مرة أخرى.")
        return
    if not network or len(network) > 32 or not all(ch.isalnum() or ch in " ._-" for ch in network):
        await message.answer("أرسل اسم شبكة صحيحًا، مثل TRC20 أو ERC20 أو BEP20 أو TON.")
        return
    await state.update_data(payment_network=network)
    await state.set_state(PaymentSG.value)
    await message.answer(
        f"<tg-emoji emoji-id='6050674936475818773'>💬</tg-emoji> تم حفظ الشبكة مؤقتًا. أرسل البيانات (الأيدي/الرقم/العنوان) لـ {safe_html(PAYMENT_METHODS[key]['name'])} الآن:",
        parse_mode="HTML",
    )


@router.message(PaymentSG.value)
async def payment_value_receive(message: Message, state: FSMContext):
    if not message.from_user or not await is_admin(message.from_user.id):
        return
    value = (message.text or "").strip()
    data = await state.get_data()
    key = data.get("payment_key")
    owner = data.get("payment_owner")
    if key not in PAYMENT_METHODS or not owner:
        await state.clear()
        await message.answer("انتهت جلسة الإعداد؛ افتح طرق الدفع وحاول مرة أخرى.")
        return
    if not value or len(value) > 256:
        await message.answer("أرسل قيمة من 1 إلى 256 حرفًا/رقمًا.")
        return
    if PAYMENT_METHODS[key].get("alnum_only") and not value.isalnum():
        await message.answer("عنوان شام كاش يقبل الحروف والأرقام فقط، بدون مسافات أو رموز.")
        return
    network = data.get("payment_network", "") if PAYMENT_METHODS[key].get("network_required") else ""
    await save_payment_wallet(owner, key, value, network)
    await state.clear()
    await message.answer("تم حفظ بيانات المحفظة.", reply_markup=back_kb(f"payment_wallet_{key}"), parse_mode="HTML")

def single_tool_kb(label, enabled, toggle_callback, icon, preview_callback=None):
    rows = [
        [InlineKeyboardButton(
            text=f"{'تعطيل' if enabled else 'تفعيل'} {label}",
            callback_data=toggle_callback,
            style="danger" if enabled else "success",
            icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133"
        )],
    ]
    if preview_callback:
        rows.append([InlineKeyboardButton(text=f"معاينة {label}", callback_data=preview_callback, style="primary")])
    rows.append([InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(F.data == "transfer_tool")
async def transfer_tool(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    enabled = bool(await get_account_setting(owner, "transfer_enabled") or 0)
    await call.message.edit_text(
        f"<tg-emoji emoji-id='5444860552310457690'>🔄</tg-emoji> <b>أكواد التحويل</b>\n\n<blockquote>الحالة الحالية: <b>{'مفعّلة' if enabled else 'معطّلة'}</b>\n\nتقدر تستقبل طلبات تحويل الرصيد من العملاء تلقائيًا.\n\nاكتب رقم الهاتف ثم المبلغ مثل: <code>01000000000 100</code></blockquote>",
        reply_markup=single_tool_kb("أكواد التحويل", enabled, "transfer_toggle", "5444860552310457690"),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "transfer_toggle")
async def transfer_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id)
    cur = await get_account_setting(owner, "transfer_enabled") or 0
    await set_account_setting(owner, "transfer_enabled", 0 if cur else 1)
    await transfer_tool(call)

@router.callback_query(F.data == "calculator_tool")
async def calculator_tool(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    enabled = bool(await get_account_setting(owner, "calculator_enabled") or 0)
    await call.message.edit_text(
        f"<tg-emoji emoji-id='5935938364086685805'>🧮</tg-emoji> <b>الآلة الحاسبة</b>\n\n<blockquote>الحالة الحالية: <b>{'مفعّلة' if enabled else 'معطّلة'}</b>\n\nاكتب عملية حسابية وسيقوم البوت بإرسال النتيجة فورًا.\n\nمثال: <code>25*4</code> أو <code>100/2</code></blockquote>",
        reply_markup=single_tool_kb("الآلة الحاسبة", enabled, "calculator_toggle", "5935938364086685805", preview_callback="calc_preview"),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "calculator_toggle")
async def calculator_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id)
    cur = await get_account_setting(owner, "calculator_enabled") or 0
    await set_account_setting(owner, "calculator_enabled", 0 if cur else 1)
    await calculator_tool(call)

def media_kb(enabled, types):
    def b(label, key):
        active = key in types
        return InlineKeyboardButton(text=label, callback_data=f"media_type_{key}", style="success" if active else "danger", icon_custom_emoji_id="6206479140040743133" if active else "6206110936789423908")
    toggle_emoji = "6206110936789423908" if enabled else "6206479140040743133"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} إدارة الميديا", callback_data="media_toggle", style="danger" if enabled else "success", icon_custom_emoji_id=toggle_emoji)],
        [b("الرسائل النصية", "text"), b("الصور", "photo")], [b("الفيديو", "video"), b("الملصقات", "sticker")],
        [b("الملفات", "document"), b("الصوتيات", "audio")], [b("البصمات", "voice"), b("الرسائل المتحركة", "animation")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

@router.callback_query(F.data == "media_manager")
async def media_manager(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    owner = await settings_owner(call.from_user.id); await ensure_account_settings(owner)
    enabled = await get_account_setting(owner, "media_enabled") or 0
    raw = await get_account_setting(owner, "media_delete_types") or "[]"
    try: types = set(json.loads(raw))
    except Exception: types = set()
    await call.message.edit_text("<tg-emoji emoji-id='5445059250382469069'>📷</tg-emoji> <b>إدارة الميديا</b>\n\n<blockquote>تقدر تتحكم في أنواع الرسائل التي يسمح بها العملاء.\n\nاضغط على أي زر لتغيير الحالة. عند التفعيل تُحذف رسائل العملاء من هذا النوع تلقائيًا.</blockquote>", reply_markup=media_kb(bool(enabled), types), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "media_toggle")
async def media_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id); cur = await get_account_setting(owner, "media_enabled") or 0
    await set_account_setting(owner, "media_enabled", 0 if cur else 1); await media_manager(call); await call.answer()

@router.callback_query(F.data.startswith("media_type_"))
async def media_type_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id); key = call.data[len("media_type_"):]
    raw = await get_account_setting(owner, "media_delete_types") or "[]"
    try: types = set(json.loads(raw))
    except Exception: types = set()
    types.remove(key) if key in types else types.add(key)
    await set_account_setting(owner, "media_delete_types", json.dumps(sorted(types))); await media_manager(call); await call.answer()

@router.callback_query(F.data == "admin_dashboard_video")
async def media_dashboard_video(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID: return
    await state.set_state(MediaSG.dashboard_video)
    await call.message.edit_text("أرسل فيديو لوحة التحكم الآن.", reply_markup=cancel_kb()); await call.answer()

@router.message(MediaSG.dashboard_video)
async def media_dashboard_video_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    if not message.video: await message.answer("أرسل فيديو فقط."); return
    await set_setting("dashboard_video_file_id", message.video.file_id)
    await set_setting("dashboard_video_type", "video")

    await set_setting("media_file_id", "")
    await set_setting("media_type", "")
    await state.clear()
    await message.answer("تم تحديث فيديو لوحة التحكم.", reply_markup=back_kb("admin_settings_section"), parse_mode="HTML")


@router.callback_query(F.data == "toggle")
async def toggle(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    row = await fetchone(conn, "SELECT enabled FROM settings WHERE owner_id=?", (OWNER_ID,))
    await conn.close()
    await call.message.edit_text(
        f"<tg-emoji emoji-id='5258476306152038031'>⚙️</tg-emoji> <b>التفعيل والتعطيل</b>\n\nالحالة الحالية: <b>{'مفعّل' if row and row['enabled'] else 'متوقف'}</b>\n\nتقدر تتحكم في تشغيل أو إيقاف البوت بالكامل من الزر الموجود بالأسفل.\n\nاختار الإجراء المطلوب:",
        reply_markup=toggle_kb(bool(row and row['enabled'])), parse_mode="HTML"
    )
    await call.answer()

async def set_bot_enabled(call: CallbackQuery, enabled: int):
    if not await is_admin(call.from_user.id):
        await call.answer("اربط حسابك أولاً.", show_alert=True)
        return
    conn = await db()
    await conn.execute("UPDATE settings SET enabled=? WHERE owner_id=?", (enabled, OWNER_ID))
    await conn.commit()
    await conn.close()
    await call.message.edit_text(
        f"<b>التفعيل والتعطيل</b>\n\nتم الآن: <b>{'تفعيل البوت' if enabled else 'تعطيل البوت'}</b>",
        reply_markup=toggle_kb(bool(enabled)), parse_mode="HTML"
    )
    await call.answer("تم الحفظ.")

@router.callback_query(F.data == "toggle_switch")
async def toggle_switch(call: CallbackQuery):
    conn = await db()
    row = await fetchone(conn, "SELECT enabled FROM settings WHERE owner_id=?", (OWNER_ID,))
    await conn.close()
    await set_bot_enabled(call, 0 if row and row["enabled"] else 1)

@router.callback_query(F.data == "toggle_on")
async def toggle_on(call: CallbackQuery):
    await set_bot_enabled(call, 1)

@router.callback_query(F.data == "toggle_off")
async def toggle_off(call: CallbackQuery):
    await set_bot_enabled(call, 0)


@router.callback_query(F.data == "section_toggle_broadcast")
async def section_toggle_broadcast(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    owner=await settings_owner(call.from_user.id); cur=await get_account_setting(owner, "broadcast_enabled") or 0
    new=0 if cur else 1; await set_account_setting(owner, "broadcast_enabled", new)
    await call.message.edit_reply_markup(reply_markup=broadcast_kb(bool(new)))
    await call.answer("تم تفعيل قسم الإذاعة" if new else "تم تعطيل قسم الإذاعة")

@router.callback_query(F.data == "section_toggle_payment")
async def section_toggle_payment(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    owner=await settings_owner(call.from_user.id); cur=await get_account_setting(owner, "payment_enabled") or 0
    new=0 if cur else 1; await set_account_setting(owner, "payment_enabled", new)
    await call.message.edit_reply_markup(reply_markup=payment_section_keyboard(PAYMENT_ENTRY_ORDER, bool(new)))
    await call.answer("تم تفعيل قسم طرق الدفع" if new else "تم تعطيل قسم طرق الدفع")

@router.callback_query(F.data.startswith("section_toggle_"))
async def section_toggle(call: CallbackQuery):
    key=call.data.removeprefix("section_toggle_")
    if key not in {"replies","words","muted","payment","broadcast"} or not await is_admin(call.from_user.id): return
    owner=await settings_owner(call.from_user.id); cur=await get_account_setting(owner, f"{key}_enabled") or 0
    await set_account_setting(owner, f"{key}_enabled", 0 if cur else 1)
    await call.answer(f"تم {'تفعيل' if not cur else 'تعطيل'} القسم")
    builders={"replies":replies_kb, "words":words_kb, "muted":muted_kb}
    if key in builders:
        await call.message.edit_reply_markup(reply_markup=builders[key](not bool(cur)))

@router.callback_query(F.data == "replies")
async def replies_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.clear()
    owner = await settings_owner(call.from_user.id)
    conn = await db()
    rows = await conn.execute_fetchall("SELECT COUNT(*) c FROM replies WHERE owner_id=?", (owner,))
    await conn.close()
    await call.message.edit_text(
        section_message("إدارة الردود التلقائية", "💬", f"عدد الردود: {rows[0]['c']}", "أضف أو عدّل الردود التلقائية من الأزرار بالأسفل."),
        reply_markup=replies_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "reply_add")
async def reply_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.update_data(reply_owner=await settings_owner(call.from_user.id))
    await state.set_state(ReplySG.add_trigger)
    await call.message.edit_text(
        "<b>إضافة رد جديد</b>\n\nالخطوة 1 من 2\nأرسل الكلمة المفتاحية.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ReplySG.add_trigger)
async def reply_get_trigger(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    trigger = (message.text or "").strip()
    if not trigger:
        await message.answer("اكتب كلمة صحيحة.")
        return
    await state.update_data(trigger=trigger.lower())
    await state.set_state(ReplySG.add_response)
    await message.answer(
        "<b>الخطوة 2 من 2</b>\n\n"
        "أرسل نص الرد (يدعم الخط العريض، المائل، الاقتباسات، الإيموجي المميز).",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )

@router.message(ReplySG.add_response)
async def reply_get_response(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    response = message.html_text or message.text or ""
    response = response.strip()
    if not response:
        await message.answer("اكتب رداً صحيحاً.")
        return
    await state.update_data(response=response, buttons=[])
    await state.set_state(ReplySG.ask_buttons)
    await message.answer(
        "<b>هل تريد إضافة أزرار تفاعلية؟</b>",
        reply_markup=reply_ask_btn_kb(), parse_mode="HTML"
    )

@router.callback_query(F.data == "reply_yes_btn")
async def reply_yes_btn(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(ReplySG.btn_label)
    await call.message.edit_text(
        "<b>إضافة زر</b>\n\nأرسل اسم الزر.\n"
        "ولإضافة إيموجي مميز، اكتب اسم الزر وضع الإيموجي بعده في نفس الرسالة.\n"
        "مثال: <code>نسخ الكود</code> ثم أرسل الإيموجي المميز بجانبه.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "reply_no_btn")
async def reply_no_btn(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await save_reply(call.message, state)

async def save_reply(message, state):
    data = await state.get_data()
    trigger = data.get("trigger")
    response = data.get("response")
    buttons = data.get("buttons", [])
    owner = data.get("reply_owner") or await settings_owner(message.from_user.id)
    conn = await db()
    cur = await conn.execute(
        "INSERT INTO replies(owner_id, trigger, response) VALUES(?, ?, ?)",
        (owner, trigger, response)
    )
    rid = cur.lastrowid
    _new_rows = {}
    for i, b in enumerate(buttons):
        _cur = await conn.execute(
            "INSERT INTO reply_buttons(reply_id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value, position) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (rid, b["label"], b["type"], b.get("color", "primary"),
             b.get("icon_custom_emoji_id", ""), b["value"], i)
        )
        if isinstance(b.get("row"), int):
            _new_rows[_cur.lastrowid] = b["row"]
    await conn.commit()
    await conn.close()
    if _new_rows and len(_new_rows) == len(buttons):
        _ROW_MAP.update(_new_rows)
        await _save_row_map()
    await state.clear()
    btns_info = ""
    if buttons:
        btns_info = "\n\n<b>الأزرار:</b>\n" + "\n".join([
            f"{b['label']} ({b['type']})" for b in buttons
        ])
    await message.answer(
        f"<b>تم حفظ الرد.</b>\n\nالكلمة: <code>{trigger}</code>\nالرد: {response}{btns_info}",
        reply_markup=back_kb("replies"), parse_mode="HTML"
    )

@router.message(ReplySG.btn_label)
async def reply_btn_label(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    label = (message.html_text or message.text or "").strip()
    if not label:
        await message.answer("اكتب اسماً صحيحاً.")
        return
    emoji_id = ""
    emoji_match = re.search(r"emoji-id\s*=\s*['\"]?(\d{6,})|\|\s*(\d{6,})$", label, re.I)
    if emoji_match:
        emoji_id = next((group for group in emoji_match.groups() if group), "")
        label = re.sub(r"\s*<tg-emoji[^>]*>.*?</tg-emoji>\s*", " ", label, flags=re.I)
        label = re.sub(r"\s*\|\s*\d{6,}\s*$", "", label).strip()
    else:
        for entity in (message.entities or []):
            if entity.type == "custom_emoji" and entity.custom_emoji_id:
                emoji_id = entity.custom_emoji_id
                break
        label = re.sub(r"\s*<tg-emoji[^>]*>.*?</tg-emoji>\s*", " ", label, flags=re.I).strip()
        if not label:
            label = (message.text or "").strip()
            if message.entities and emoji_id:
                label = re.sub(r"\s+", " ", label).strip()
    if not label:
        await message.answer("اكتب اسم الزر بجانب الإيموجي المميز.")
        return
    await state.update_data(current_btn_label=label, current_btn_emoji_id=emoji_id)
    await state.set_state(ReplySG.btn_type)
    await message.answer(
        f"<b>اسم الزر:</b> {label}\n\nاختر النوع:",
        reply_markup=reply_btn_type_kb(), parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("btn_type_"))
async def reply_btn_type(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    btn_type = call.data.split("btn_type_")[1]
    await state.update_data(current_btn_type=btn_type)
    names = {"text": "نص", "url": "رابط", "copy": "نسخ"}
    await state.set_state(ReplySG.btn_value)
    if btn_type == "url":
        hint = "أرسل الرابط (يجب أن يبدأ بـ http:// أو https://)."
    elif btn_type == "copy":
        hint = "أرسل النص الذي سيتم نسخه عند الضغط."
    else:
        hint = "أرسل النص الذي سيُرسل للعميل عند الضغط."
    await call.message.edit_text(
        f"<b>النوع:</b> {names.get(btn_type, btn_type)}\n\n{hint}",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("btn_color_"))
async def reply_btn_color(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    color_key = call.data.split("btn_color_")[1]
    data = await state.get_data()
    btype = data.get("current_btn_type")
    value = data.get("current_btn_value")
    label = data.get("current_btn_label")
    if not value or not label:
        await call.answer("ابدأ إضافة الزر من جديد.", show_alert=True)
        return
    style = BTN_STYLE_MAP.get(color_key, "primary")
    btn = {
        "label": label,
        "type": btype,
        "color": style,
        "icon_custom_emoji_id": data.get("current_btn_emoji_id", ""),
        "value": value,
    }
    buttons = data.get("buttons", [])
    buttons.append(btn)
    await state.update_data(buttons=buttons, current_btn_value=None)
    await state.set_state(ReplySG.ask_more)
    type_name = {"text": "نص", "url": "رابط", "copy": "نسخ"}.get(btype, btype)
    await call.message.edit_text(
        f"<b>تم إضافة الزر:</b>\n"
        f"الاسم: {btn['label']}\n"
        f"النوع: {type_name}\n"
        f"اللون: {STYLE_LABEL.get(style, style)}\n"
        f"عدد الأزرار الآن: <b>{len(buttons)}</b>\n\n"
        "هل تريد إضافة زر آخر؟",
        reply_markup=reply_more_kb(), parse_mode="HTML"
    )
    await call.answer()


@router.message(ReplySG.btn_value)
async def reply_btn_value(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    value = (message.text or "").strip()
    if not value:
        await message.answer("اكتب قيمة صحيحة.")
        return
    data = await state.get_data()
    btype = data.get("current_btn_type")
    if btype == "url" and not (value.startswith("http://") or value.startswith("https://")):
        await message.answer("الرابط يجب أن يبدأ بـ http:// أو https://")
        return
    # الخطوة التالية: اختيار لون الزر
    await state.update_data(current_btn_value=value)
    await state.set_state(ReplySG.btn_color)
    await message.answer(
        "<b>اختر لون الزر:</b>",
        reply_markup=reply_btn_color_kb(), parse_mode="HTML"
    )

@router.callback_query(F.data == "reply_add_more_btn")
async def reply_add_more(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(ReplySG.btn_label)
    await call.message.edit_text(
        "<b>إضافة زر جديد</b>\n\nأرسل اسم الزر.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "reply_save_btn")
async def reply_save_btn(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await call.answer("جاري الحفظ...")
    await save_reply(call.message, state)

@router.callback_query(F.data == "reply_list")
async def reply_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, trigger, response FROM replies WHERE owner_id=? ORDER BY id DESC", (owner,)
    )
    if not rows:
        await conn.close()
        await call.message.edit_text("لا توجد ردود.", reply_markup=replies_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") is not None else 1)), parse_mode="HTML")
        await call.answer()
        return
    parts = []
    for r in rows:
        btns = await conn.execute_fetchall(
            "SELECT label, btn_type, btn_color FROM reply_buttons WHERE reply_id=? ORDER BY position",
            (r["id"],)
        )
        part = f"<b>#{r['id']}</b>\nالكلمة: <code>{r['trigger']}</code>\nالرد: {r['response']}"
        if btns:
            part += "\n<b>الأزرار:</b>\n" + "\n".join([
                f"{b['label']} ({b['btn_type']})" for b in btns
            ])
        parts.append(part)
    await conn.close()
    await call.message.edit_text(
        "<b>قائمة الردود</b>\n\n" + "\n\n".join(parts),
        reply_markup=replies_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "reply_edit_list")
async def reply_edit_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, trigger FROM replies WHERE owner_id=? ORDER BY id DESC LIMIT 30", (owner,)
    )
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد ردود للتعديل.", reply_markup=replies_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") is not None else 1)), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['trigger']}", callback_data=f"redit_{r['id']}", style="primary", icon_custom_emoji_id="5888880224195581055")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="replies", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر الرد:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(
    F.data.startswith("redit_") & ~F.data.startswith("redit_trigger_")
    & ~F.data.startswith("redit_response_") & ~F.data.startswith("redit_clearbtns_") & ~F.data.startswith("redit_btncolors_")
)
async def reply_edit_menu(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    owner = await settings_owner(call.from_user.id)
    conn = await db()
    row = await fetchone(conn,
        "SELECT id, trigger, response FROM replies WHERE id=? AND owner_id=?", (rid, owner))
    if not row:
        await conn.close()
        await call.answer("غير موجود.", show_alert=True)
        return
    btns = await conn.execute_fetchall(
        "SELECT label, btn_type, btn_color FROM reply_buttons WHERE reply_id=? ORDER BY position", (rid,))
    await conn.close()
    btns_txt = "\n\n<b>الأزرار:</b>\n" + "\n".join([
        f"{b['label']} ({b['btn_type']})" for b in btns
    ]) if btns else "\n\nلا توجد أزرار."
    await call.message.edit_text(
        f"<b>تعديل الرد #{rid}</b>\n\nالكلمة: <code>{row['trigger']}</code>\nالرد: {row['response']}{btns_txt}",
        reply_markup=reply_edit_kb(rid), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("redit_trigger_"))
async def redit_trigger(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    await state.update_data(edit_rid=rid)
    await state.set_state(ReplySG.edit_trigger)
    await call.message.edit_text(
        "<b>تعديل الكلمة المفتاحية</b>\n\nأرسل الكلمة الجديدة.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ReplySG.edit_trigger)
async def redit_trigger_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    text = (message.text or "").strip().lower()
    if not text:
        await message.answer("اكتب كلمة صحيحة.")
        return
    data = await state.get_data()
    owner = await settings_owner(message.from_user.id)
    conn = await db()
    await conn.execute("UPDATE replies SET trigger=? WHERE id=? AND owner_id=?",
                       (text, data.get("edit_rid"), owner))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(f"تم التعديل: <code>{text}</code>", reply_markup=back_kb("replies"), parse_mode="HTML")

@router.callback_query(F.data.startswith("redit_response_"))
async def redit_response(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    await state.update_data(edit_rid=rid)
    await state.set_state(ReplySG.edit_response)
    await call.message.edit_text(
        "<b>تعديل نص الرد</b>\n\nأرسل النص الجديد.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ReplySG.edit_response)
async def redit_response_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    text = message.html_text or message.text or ""
    text = text.strip()
    if not text:
        await message.answer("اكتب رداً صحيحاً.")
        return
    data = await state.get_data()
    owner = await settings_owner(message.from_user.id)
    conn = await db()
    await conn.execute("UPDATE replies SET response=? WHERE id=? AND owner_id=?",
                       (text, data.get("edit_rid"), owner))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer("تم تعديل نص الرد.", reply_markup=back_kb("replies"), parse_mode="HTML")

@router.callback_query(F.data.startswith("redit_btncolors_"))
async def redit_btncolors(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    rid=int(call.data.rsplit("_",1)[-1])
    conn=await db()
    rows=await conn.execute_fetchall("SELECT id,label,btn_color FROM reply_buttons WHERE reply_id=? ORDER BY position",(rid,))
    await conn.close()
    if not rows:
        await call.answer("لا توجد أزرار لهذا الرد.",show_alert=True); return
    kb=[]
    for row in rows:
        kb.append([InlineKeyboardButton(text=f"{row['label']} — {STYLE_LABEL.get(row['btn_color'],row['btn_color'])}",callback_data=f"rbtncolor_{row['id']}",style=BTN_STYLE_MAP.get(row['btn_color'],'primary'))])
    kb.append([InlineKeyboardButton(text="رجوع",callback_data=f"redit_{rid}",style="danger")])
    await call.message.edit_text("اختر الزر الذي تريد تغيير لونه:",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@router.callback_query(F.data.startswith("rbtncolor_"))
async def redit_btncolor_pick(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    bid=int(call.data.rsplit("_",1)[-1])
    conn=await db(); row=await fetchone(conn,"SELECT reply_id,label FROM reply_buttons WHERE id=?",(bid,)); await conn.close()
    if not row: await call.answer("الزر غير موجود.",show_alert=True); return
    kb=[]
    for color,label in (("danger","أحمر"),("success","أخضر"),("primary","أزرق")):
        kb.append([InlineKeyboardButton(text=label,callback_data=f"rbtnset_{bid}_{color}",style=color)])
    kb.append([InlineKeyboardButton(text="رجوع",callback_data=f"redit_btncolors_{row['reply_id']}",style="danger")])
    await call.message.edit_text(f"اختر اللون الجديد للزر: <b>{row['label']}</b>",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("rbtnset_"))
async def redit_btncolor_save(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    try: _,bid_raw,color=call.data.split("_",2); bid=int(bid_raw)
    except Exception: await call.answer(); return
    if color not in {"danger","success","primary"}: await call.answer(); return
    conn=await db(); row=await fetchone(conn,"SELECT reply_id FROM reply_buttons WHERE id=?",(bid,))
    if row:
        await conn.execute("UPDATE reply_buttons SET btn_color=? WHERE id=?",(color,bid)); await conn.commit()
    await conn.close()
    if not row: await call.answer("الزر غير موجود.",show_alert=True); return
    await call.answer("تم تغيير لون الزر وحفظه.")
    call.data=f"redit_btncolors_{row['reply_id']}"
    await redit_btncolors(call)

@router.callback_query(F.data.startswith("redit_clearbtns_"))
async def redit_clear(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    conn = await db()
    await conn.execute("DELETE FROM reply_buttons WHERE reply_id=?", (rid,))
    await conn.commit()
    await conn.close()
    await call.answer("تم حذف الأزرار.", show_alert=True)
    call.data = f"redit_{rid}"
    await reply_edit_menu(call)

@router.callback_query(F.data == "reply_del_list")
async def reply_del_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, trigger FROM replies WHERE owner_id=? ORDER BY id DESC LIMIT 30", (owner,))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد ردود.", reply_markup=replies_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "replies_enabled") is not None else 1)), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['trigger']}", callback_data=f"rdel_{r['id']}", style="danger", icon_custom_emoji_id="6039522349517115015")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="replies", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر الرد للحذف:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("rdel_"))
async def reply_del_confirm(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    conn = await db()
    row = await fetchone(conn, "SELECT trigger FROM replies WHERE id=? AND owner_id=?", (rid, await settings_owner(call.from_user.id)))
    await conn.close()
    if not row:
        await call.answer("غير موجود.", show_alert=True)
        return
    await call.message.edit_text(
        f"<b>تأكيد الحذف</b>\n\n<code>{row['trigger']}</code>",
        reply_markup=confirm_kb("rdel", str(rid)), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "words")
async def words_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.clear()
    conn = await db()
    rows = await conn.execute_fetchall("SELECT COUNT(*) c FROM banned_words WHERE owner_id=?", (await settings_owner(call.from_user.id),))
    await conn.close()
    await call.message.edit_text(
        section_message("الكلمات الممنوعة", "🚫", f"عدد الكلمات: {rows[0]['c']}", "أضف الكلمات التي تريد منعها أو عدّل القائمة من الأسفل."),
        reply_markup=words_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "word_add")
async def word_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WordSG.add_word)
    await call.message.edit_text(
        "<b>إضافة كلمة ممنوعة</b>\n\nأرسل الكلمة.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(WordSG.add_word)
async def word_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    w = (message.text or "").strip().lower()
    if not w:
        await message.answer("اكتب كلمة صحيحة.")
        return
    conn = await db()
    await conn.execute("INSERT INTO banned_words(owner_id, word) VALUES(?, ?)", (await settings_owner(message.from_user.id), w))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(f"تمت الإضافة: <code>{w}</code>", reply_markup=back_kb("words"), parse_mode="HTML")

@router.callback_query(F.data == "word_list")
async def word_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, word FROM banned_words WHERE owner_id=? ORDER BY id DESC", (await settings_owner(call.from_user.id),))
    await conn.close()
    body = "\n".join([f"<b>#{r['id']}</b> - <code>{r['word']}</code>" for r in rows]) or "لا توجد كلمات."
    await call.message.edit_text(
        "<b>قائمة الكلمات</b>\n\n" + body, reply_markup=words_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "word_edit_list")
async def word_edit_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, word FROM banned_words WHERE owner_id=? ORDER BY id DESC LIMIT 30", (await settings_owner(call.from_user.id),))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد كلمات.", reply_markup=words_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") is not None else 1)), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['word']}", callback_data=f"wedit_{r['id']}", style="primary", icon_custom_emoji_id="5257991477358763590")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="words", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر الكلمة:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("wedit_"))
async def word_edit(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    wid = int(call.data.split("_")[-1])
    await state.update_data(edit_wid=wid)
    await state.set_state(WordSG.edit_word)
    await call.message.edit_text(
        "<b>تعديل الكلمة</b>\n\nأرسل الكلمة الجديدة.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(WordSG.edit_word)
async def word_edit_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    w = (message.text or "").strip().lower()
    if not w:
        await message.answer("اكتب كلمة صحيحة.")
        return
    data = await state.get_data()
    conn = await db()
    await conn.execute("UPDATE banned_words SET word=? WHERE id=? AND owner_id=?",
                       (w, data.get("edit_wid"), await settings_owner(message.from_user.id)))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(f"تم التعديل: <code>{w}</code>", reply_markup=back_kb("words"), parse_mode="HTML")

@router.callback_query(F.data == "word_del_list")
async def word_del_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, word FROM banned_words WHERE owner_id=? ORDER BY id DESC LIMIT 30", (await settings_owner(call.from_user.id),))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد كلمات.", reply_markup=words_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "words_enabled") is not None else 1)), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['word']}", callback_data=f"wdel_{r['id']}", style="danger", icon_custom_emoji_id="5258130763148172425")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="words", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر الكلمة للحذف:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("wdel_"))
async def word_del_confirm(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    wid = int(call.data.split("_")[-1])
    conn = await db()
    row = await fetchone(conn, "SELECT word FROM banned_words WHERE id=? AND owner_id=?", (wid, await settings_owner(call.from_user.id)))
    await conn.close()
    if not row:
        await call.answer("غير موجودة.", show_alert=True)
        return
    await call.message.edit_text(
        f"<b>تأكيد الحذف</b>\n\n<code>{row['word']}</code>",
        reply_markup=confirm_kb("wdel", str(wid)), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "muted")
async def muted_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.clear()
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT COUNT(*) c FROM muted WHERE connection_id IN "
        "(SELECT connection_id FROM business WHERE user_id=?) "
        "AND chat_id NOT IN (?)",
        (OWNER_ID, OWNER_ID))
    await conn.close()
    await call.message.edit_text(
        section_message("إدارة المكتومين", "🔇", f"عدد المكتومين: {rows[0]['c']}", "للكتم: اكتب كلمة (كتم) في الشات.", "لإلغاء الكتم: اكتب كلمة (الغاء الكتم) في الشات."),
        reply_markup=muted_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "mute_add")
async def mute_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.set_state(MuteSG.chat_id)
    await call.message.edit_text("<b>كتم عميل</b>\n\nأرسل آيدي العميل أو آيدي محادثة Business المراد كتمه.", reply_markup=cancel_kb(), parse_mode="HTML")
    await call.answer()

@router.message(MuteSG.chat_id)
async def mute_add_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    try: cid=int((message.text or '').strip())
    except: await message.answer("أرسل آيدي رقمي صحيح."); return
    if cid == OWNER_ID:
        await state.clear()
        await message.answer("<blockquote><b>هذا الحساب محمي ولا يمكن كتمه.</b></blockquote>", reply_markup=back_kb("muted"), parse_mode="HTML")
        return
    conn=await db(); rows=await conn.execute_fetchall("SELECT connection_id FROM business WHERE user_id=? AND enabled=1", (message.from_user.id,))
    if not rows:
        await conn.close(); await state.clear(); await message.answer("لا يوجد حساب Business مرتبط.", reply_markup=back_kb("muted"), parse_mode="HTML"); return
    for row in rows:
        await conn.execute("INSERT OR IGNORE INTO muted(connection_id, chat_id) VALUES(?, ?)", (row["connection_id"], cid))
    await conn.commit(); await conn.close(); await state.clear(); await message.answer(f"تم كتم العميل <code>{cid}</code>.", reply_markup=back_kb("muted"), parse_mode="HTML")

@router.callback_query(F.data == "mute_list")
async def mute_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT chat_id FROM muted WHERE connection_id IN "
        "(SELECT connection_id FROM business WHERE user_id=?) "
        "AND chat_id NOT IN (?)",
        (call.from_user.id, call.from_user.id))
    await conn.close()
    body = "\n".join([f"<code>{r['chat_id']}</code>" for r in rows]) or "فارغة."
    await call.message.edit_text(
        "<b>المكتومين</b>\n\n" + body, reply_markup=muted_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "mute_unmute_list")
async def mute_unmute_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT chat_id FROM muted WHERE connection_id IN "
        "(SELECT connection_id FROM business WHERE user_id=?) "
        "AND chat_id NOT IN (?)",
        (call.from_user.id, call.from_user.id))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا يوجد مكتومين.", reply_markup=muted_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "muted_enabled") is not None else 1)), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=str(r["chat_id"]), callback_data=f"munmute_{r['chat_id']}", style="primary", icon_custom_emoji_id="5444988177263654261")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="muted", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر العميل:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("munmute_"))
async def mute_unmute(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    conn = await db()
    await conn.execute("DELETE FROM muted WHERE chat_id=?", (cid,))
    await conn.commit()
    await conn.close()
    await call.answer("تم رفع الكتم.")
    await mute_unmute_list(call)


def account_force_kb(enabled=True):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} الاشتراك الإجباري", callback_data="account_force_toggle", style="danger" if enabled else "success", icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="حذف قناة من الحساب", callback_data="account_force_del_list", style="danger", icon_custom_emoji_id="6039522349517115015"), InlineKeyboardButton(text="إضافة قناة للحساب", callback_data="account_force_add", style="primary", icon_custom_emoji_id="5778455936410588193")],
        [InlineKeyboardButton(text="عرض قنوات الحساب", callback_data="account_force_list", style="primary", icon_custom_emoji_id="6039391078136681499")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5895383238473421210")]
    ])

@router.callback_query(F.data == "account_force")
async def account_force(call: CallbackQuery, state: FSMContext):
    if not await is_account_linked(call.from_user.id): return
    owner=call.from_user.id; conn=await db(); row=await fetchone(conn, "SELECT COUNT(*) c FROM force_channels WHERE owner_id=? AND scope='account'", (owner,)); await conn.close()
    enabled=bool(await get_account_setting(owner, "account_force_enabled") if await get_account_setting(owner, "account_force_enabled") is not None else 1)
    await call.message.edit_text(f"<b>الاشتراك الإجباري للحساب</b>\n\n<blockquote>الحالة: <b>{'مفعّل' if enabled else 'معطّل'}</b>\nعدد القنوات: <b>{row['c']}</b>\nهذه القنوات تخص حسابك فقط.</blockquote>", reply_markup=account_force_kb(enabled), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "account_force_toggle")
async def account_force_toggle(call: CallbackQuery):
    if not await is_account_linked(call.from_user.id): return
    owner=call.from_user.id; cur=await get_account_setting(owner, "account_force_enabled") or 0
    await set_account_setting(owner, "account_force_enabled", 0 if cur else 1)
    await call.message.edit_text("<b>تم تحديث حالة الاشتراك الإجباري للحساب.</b>", reply_markup=back_kb("account_force"), parse_mode="HTML")

@router.callback_query(F.data == "account_force_add")
async def account_force_add(call: CallbackQuery, state: FSMContext):
    if not await is_account_linked(call.from_user.id): return
    await state.update_data(force_owner=call.from_user.id, force_scope="account"); await state.set_state(ForceSG.add_channel)
    await call.message.edit_text("<b>إضافة قناة للحساب</b>\n\nأرسل @username أو -100...", reply_markup=cancel_kb(), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "account_force_list")
async def account_force_list(call: CallbackQuery):
    owner=call.from_user.id; conn=await db(); rows=await conn.execute_fetchall("SELECT id, title, channel FROM force_channels WHERE owner_id=? AND scope='account' ORDER BY id", (owner,)); await conn.close()
    body="\n\n".join(f"<b>#{r['id']} {safe_html(r['title'])}</b>\n<code>{safe_html(r['channel'])}</code>" for r in rows) or "لا توجد قنوات."
    await call.message.edit_text("<b>قنوات الاشتراك الإجباري للحساب</b>\n\n"+body, reply_markup=account_force_kb(), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "account_force_del_list")
async def account_force_del_list(call: CallbackQuery):
    if not await is_account_linked(call.from_user.id):
        return
    conn = await db()
    rows = await conn.execute_fetchall("SELECT id, title FROM force_channels WHERE owner_id=? AND scope='account' ORDER BY id", (call.from_user.id,))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد قنوات لحذفها.", reply_markup=account_force_kb(), parse_mode="HTML")
        await call.answer()
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['title']}", callback_data=f"afdel_{r['id']}", style="danger", icon_custom_emoji_id="6039522349517115015")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="account_force", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text("<b>اختر قناة الحذف:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("afdel_"))
async def account_force_del_confirm(call: CallbackQuery):
    if not await is_account_linked(call.from_user.id):
        return
    fid = int(call.data.split("_")[-1])
    conn = await db()
    row = await fetchone(conn, "SELECT title FROM force_channels WHERE id=? AND owner_id=? AND scope='account'", (fid, call.from_user.id))
    await conn.close()
    if not row:
        await call.answer("القناة غير موجودة.", show_alert=True)
        return
    await call.message.edit_text(f"<b>تأكيد حذف القناة</b>\n\n{safe_html(row['title'])}", reply_markup=confirm_kb("afdel", str(fid)), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "force")
async def force_menu(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.clear()
    conn = await db()
    rows = await conn.execute_fetchall("SELECT COUNT(*) c FROM force_channels WHERE owner_id=? AND scope='bot'", (OWNER_ID,))
    await conn.close()
    await call.message.edit_text(
        f"<b>الاشتراك الإجباري</b>\n\nعدد القنوات: <b>{rows[0]['c']}</b>\n\n"
        "يجب أن يكون البوت مشرفاً في القناة.",
        reply_markup=force_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "force_add")
async def force_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.update_data(force_owner=OWNER_ID, force_scope="bot")
    await state.set_state(ForceSG.add_channel)
    await call.message.edit_text(
        "<b>إضافة قناة</b>\n\nالخطوة 1 من 2\nأرسل المعرف:\n"
        "<code>@username</code> أو <code>-1001234567890</code>",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ForceSG.add_channel)
async def force_get_channel(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    ch = (message.text or "").strip()
    if not ch:
        await message.answer("اكتب معرف صحيح.")
        return
    try:
        channel_chat = await message.bot.get_chat(chat_id=ch)
        channel_title = channel_chat.title or channel_chat.full_name or ch
    except Exception:
        await message.answer(
            "لم أستطع الوصول إلى القناة. تأكد أن البوت مشرف فيها وأن المعرف صحيح، ثم أرسل المعرف مرة أخرى.",
            reply_markup=cancel_kb(), parse_mode="HTML"
        )
        return
    data = await state.get_data()
    return_callback = "account_force" if data.get("force_scope") == "account" else "force"
    conn = await db()
    await conn.execute(
        "INSERT INTO force_channels(owner_id, channel, title, scope) VALUES(?, ?, ?, ?)",
        (data.get("force_owner", OWNER_ID), ch, channel_title, data.get("force_scope", "account"))
    )
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(
        f"تمت إضافة القناة تلقائياً باسم: <b>{safe_html(channel_title)}</b>\n\n"
        f"المعرف: <code>{safe_html(ch)}</code>",
        reply_markup=back_kb(return_callback), parse_mode="HTML"
    )

@router.message(ForceSG.add_title)
async def force_get_title(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("اكتب عنواناً صحيحاً.")
        return
    data = await state.get_data()
    return_callback = "account_force" if data.get("force_scope") == "account" else "force"
    conn = await db()
    await conn.execute(
        "INSERT INTO force_channels(owner_id, channel, title, scope) VALUES(?, ?, ?, ?)",
        (data.get("force_owner", OWNER_ID), data.get("channel"), title, data.get("force_scope", "account")))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(
        f"تمت الإضافة.\n\nالمعرف: <code>{data.get('channel')}</code>\nالعنوان: {title}",
        reply_markup=back_kb(return_callback), parse_mode="HTML"
    )

@router.callback_query(F.data == "force_list")
async def force_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, channel, title FROM force_channels WHERE owner_id=? AND scope='bot'", (OWNER_ID,))
    await conn.close()
    body = "\n\n".join([
        f"<b>#{r['id']}</b>\nالمعرف: <code>{r['channel']}</code>\nالعنوان: {r['title']}"
        for r in rows
    ]) or "لا توجد قنوات."
    await call.message.edit_text(
        "<b>قنوات الاشتراك الإجباري</b>\n\n" + body,
        reply_markup=force_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "force_edit_list")
async def force_edit_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, title FROM force_channels WHERE owner_id=? AND scope='bot'", (OWNER_ID,))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد قنوات.", reply_markup=force_kb(), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['title']}", callback_data=f"fedit_{r['id']}", style="primary", icon_custom_emoji_id="5888620056551625531")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="force", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر القناة:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(
    F.data.startswith("fedit_") & ~F.data.startswith("fedit_channel_") & ~F.data.startswith("fedit_title_")
)
async def force_edit_menu(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    fid = int(call.data.split("_")[-1])
    conn = await db()
    row = await fetchone(conn,
        "SELECT channel, title FROM force_channels WHERE id=? AND owner_id=? AND scope='bot'", (fid, OWNER_ID))
    await conn.close()
    if not row:
        await call.answer("غير موجودة.", show_alert=True)
        return
    await call.message.edit_text(
        f"<b>تعديل القناة #{fid}</b>\n\nالمعرف: <code>{row['channel']}</code>\nالعنوان: {row['title']}",
        reply_markup=force_edit_kb(fid), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("fedit_channel_"))
async def force_edit_channel(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    fid = int(call.data.split("_")[-1])
    await state.update_data(edit_fid=fid)
    await state.set_state(ForceSG.edit_channel)
    await call.message.edit_text(
        "<b>تعديل المعرف</b>\n\nأرسل المعرف الجديد.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ForceSG.edit_channel)
async def force_edit_channel_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    ch = (message.text or "").strip()
    if not ch:
        await message.answer("اكتب معرف صحيح.")
        return
    data = await state.get_data()
    conn = await db()
    await conn.execute("UPDATE force_channels SET channel=? WHERE id=? AND owner_id=? AND scope='bot'",
                       (ch, data.get("edit_fid"), OWNER_ID))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(f"تم التعديل: <code>{ch}</code>", reply_markup=back_kb("force"), parse_mode="HTML")

@router.callback_query(F.data.startswith("fedit_title_"))
async def force_edit_title(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    fid = int(call.data.split("_")[-1])
    await state.update_data(edit_fid=fid)
    await state.set_state(ForceSG.edit_title)
    await call.message.edit_text(
        "<b>تعديل العنوان</b>\n\nأرسل العنوان الجديد.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(ForceSG.edit_title)
async def force_edit_title_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("اكتب عنواناً صحيحاً.")
        return
    data = await state.get_data()
    conn = await db()
    await conn.execute("UPDATE force_channels SET title=? WHERE id=? AND owner_id=? AND scope='bot'",
                       (title, data.get("edit_fid"), OWNER_ID))
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(f"تم التعديل: <code>{title}</code>", reply_markup=back_kb("force"), parse_mode="HTML")

@router.callback_query(F.data == "force_del_list")
async def force_del_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, title FROM force_channels WHERE owner_id=? AND scope='bot'", (OWNER_ID,))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد قنوات.", reply_markup=force_kb(), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=f"#{r['id']} - {r['title']}", callback_data=f"fdel_{r['id']}", style="danger", icon_custom_emoji_id="6039522349517115015")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="force", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر القناة للحذف:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("fdel_"))
async def force_del_confirm(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    fid = int(call.data.split("_")[-1])
    conn = await db()
    row = await fetchone(conn,
        "SELECT title FROM force_channels WHERE id=? AND owner_id=? AND scope='bot'", (fid, OWNER_ID))
    await conn.close()
    if not row:
        await call.answer("غير موجودة.", show_alert=True)
        return
    await call.message.edit_text(
        f"<b>تأكيد الحذف</b>\n\n{row['title']}",
        reply_markup=confirm_kb("fdel", str(fid)), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_action(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[1]
    item_id = int(parts[2])
    if action == "afdel" and not await is_account_linked(call.from_user.id):
        await call.answer("هذه العملية للحساب المرتبط فقط.", show_alert=True)
        return
    if action == "fdel" and call.from_user.id != OWNER_ID:
        await call.answer("هذه العملية للمالك فقط.", show_alert=True)
        return
    conn = await db()
    if action == "rdel":
        owner = await settings_owner(call.from_user.id)
        await conn.execute("DELETE FROM replies WHERE id=? AND owner_id=?", (item_id, owner))
        await conn.execute("DELETE FROM reply_buttons WHERE reply_id=?", (item_id,))
    elif action == "wdel":
        await conn.execute("DELETE FROM banned_words WHERE id=? AND owner_id=?", (item_id, await settings_owner(call.from_user.id)))
    elif action == "fdel":
        await conn.execute("DELETE FROM force_channels WHERE id=? AND owner_id=? AND scope='bot'", (item_id, OWNER_ID))
    elif action == "afdel":
        await conn.execute("DELETE FROM force_channels WHERE id=? AND owner_id=? AND scope='account'", (item_id, call.from_user.id))
    elif action == "adel":
        await conn.execute("DELETE FROM admins WHERE user_id=?", (item_id,))
    await conn.commit()
    await conn.close()
    await call.answer("تم الحذف.")
    await show_main(call)


@router.callback_query(F.data == "broadcast")
async def broadcast_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.clear()
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT COUNT(*) c FROM customers WHERE connection_id IN "
        "(SELECT connection_id FROM business WHERE user_id=?)", (await settings_owner(call.from_user.id),))
    await conn.close()
    await call.message.edit_text(
        f"<b>الإذاعة للعملاء</b>\n\nعدد العملاء: <b>{rows[0]['c']}</b>",
        reply_markup=broadcast_kb(bool(await get_account_setting(await settings_owner(call.from_user.id), "broadcast_enabled") if await get_account_setting(await settings_owner(call.from_user.id), "broadcast_enabled") is not None else 1)), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(BroadcastSG.add_text)
    await call.message.edit_text(
        "<b>إرسال رسالة جماعية</b>\n\nأرسل النص أو الصورة أو الفيديو.\n"
        "التنسيق الكامل (عريض/مائل/اقتباس/إيموجي مميز) مدعوم.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(BroadcastSG.add_text)
async def broadcast_do(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    text = message.html_text or message.caption or ""
    text = text.strip()
    if not text and not message.photo and not message.video and not message.voice and not message.audio:
        await message.answer("اكتب نصاً أو أرسل ميديا.")
        return
    await _bc_stage(message, state, "customers", text, _bc_extract_media(message, ("photo", "video", "voice", "audio")),
                    owner=await settings_owner(message.from_user.id))

@router.message(ChannelBroadcastSG.add_text)
async def admin_channel_broadcast_do(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    text = (message.html_text or message.caption or "").strip()
    if not text and not any((message.photo, message.video, message.voice, message.audio, message.document, message.animation)):
        await message.answer("اكتب نصاً أو أرسل ميديا.")
        return
    await _bc_stage(message, state, "channels", text, _bc_extract_media(message, _BC_MEDIA_ORDER))

@router.callback_query(F.data == "admin_bot_broadcast")
async def admin_bot_broadcast(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await state.set_state(BotBroadcastSG.add_text)
    conn = await db()
    row = await fetchone(conn, "SELECT COUNT(*) c FROM bot_users WHERE user_id!=?", (OWNER_ID,))
    await conn.close()
    await call.message.edit_text(
        f"<b>إذاعة مستخدمي البوت</b>\n\nعدد المستخدمين: <b>{row['c'] if row else 0}</b>\n\n"
        "أرسل النص أو الصورة أو الفيديو أو الصوت أو البصمة لإرسالها لمستخدمي البوت فقط.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(BotBroadcastSG.add_text)
async def admin_bot_broadcast_do(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    text = (message.html_text or message.caption or "").strip()
    if not text and not any((message.photo, message.video, message.voice, message.audio, message.document, message.animation)):
        await message.answer("اكتب نصاً أو أرسل ميديا.")
        return
    await _bc_stage(message, state, "bot", text, _bc_extract_media(message, _BC_MEDIA_ORDER))

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "welcome")
async def welcome_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.clear()
    owner = await settings_owner(call.from_user.id); await ensure_account_settings(owner)
    conn = await db(); row = await fetchone(conn, "SELECT welcome, welcome_enabled, welcome_mode, welcome_sticker_file_id, welcome_image_file_id FROM settings WHERE owner_id=?", (owner,)); await conn.close()
    cur = row["welcome"] or "لا يوجد"
    sticker_status = "مضاف" if row["welcome_sticker_file_id"] else "غير مضاف"
    image_status = "مضافة" if row["welcome_image_file_id"] else "غير مضافة"
    await call.message.edit_text(
        section_message("رسالة الترحيب", "👋", f"الحالة: {'مفعّلة' if row['welcome_enabled'] else 'معطّلة'}", f"الوضع: {'عند عدم الاتصال فقط' if row['welcome_mode']=='offline' else 'دائماً'}", f"النص الحالي: {cur}", f"الملصق المصاحب: {sticker_status}", f"الصورة المصاحبة: {image_status}", "يمكنك إضافة نص وصورة وملصق، وسيتم إرسال الصورة مع النص والملصق كرسائل منفصلة."),
        reply_markup=welcome_kb(bool(row['welcome_enabled']), row['welcome_mode']),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "welcome_toggle")
async def welcome_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id); cur = await get_account_setting(owner, "welcome_enabled") or 0
    new_value = 0 if cur else 1
    await set_account_setting(owner, "welcome_enabled", new_value)
    mode = await get_account_setting(owner, "welcome_mode") or "always"
    await call.message.edit_reply_markup(reply_markup=welcome_kb(bool(new_value), mode))
    await call.answer("تم تعطيل رسالة الترحيب" if not new_value else "تم تفعيل رسالة الترحيب")

@router.callback_query(F.data == "welcome_mode")
async def welcome_mode(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id); cur = await get_account_setting(owner, "welcome_mode") or "always"
    new_mode = "always" if cur == "offline" else "offline"
    await set_account_setting(owner, "welcome_mode", new_mode)
    enabled = bool(await get_account_setting(owner, "welcome_enabled") or 0)
    await call.message.edit_reply_markup(reply_markup=welcome_kb(enabled, new_mode))
    await call.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم تحديث وضع رسالة الترحيب")

@router.callback_query(F.data == "welcome_set")
async def welcome_set(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WelcomeSG.set_text)
    await call.message.edit_text(
        "<b>تعديل رسالة الترحيب</b>\n\nأرسل النص الجديد.\n"
        "يمكنك إرسال نص منسق باستخدام تيليجرام، وسيتم إرسال الملصق بشكل منفصل إذا تمت إضافته.",
        reply_markup=cancel_kb("advanced"), parse_mode="HTML"
    )
    await call.answer()

@router.message(WelcomeSG.set_text)
async def welcome_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    text = message.html_text or message.text or ""
    text = text.strip()
    if not text:
        await message.answer("<tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> من فضلك اكتب نصاً صحيحاً.")
        return
    await set_account_setting(await settings_owner(message.from_user.id), "welcome", text)
    await state.update_data(welcome_buttons=[])
    await state.set_state(WelcomeSG.ask_buttons)
    await message.answer("هل تريد إضافة أزرار أسفل رسالة الترحيب؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نعم، إضافة أزرار", callback_data="welcome_btn_yes", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="تخطي", callback_data="welcome_btn_no", style="danger", icon_custom_emoji_id="6030445631921721471")]
    ]), parse_mode="HTML")

@router.callback_query(F.data == "welcome_btn_yes")
async def welcome_btn_yes(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.set_state(WelcomeSG.btn_label)
    await call.message.edit_text("أرسل اسم الزر. ويمكنك إرفاق إيموجي مميز بنفس طريقة أزرار الردود التلقائية.", reply_markup=cancel_kb("welcome"), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "welcome_btn_no")
async def welcome_btn_no(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.update_data(welcome_buttons=[])
    await _welcome_continue_after_buttons(call.message, state)
    await call.answer()

@router.message(WelcomeSG.btn_label)
async def welcome_btn_label(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    label=(message.html_text or message.text or "").strip()
    if not label:
        await message.answer("اكتب اسم الزر."); return
    emoji_id=""
    for entity in (message.entities or []):
        if entity.type == "custom_emoji" and entity.custom_emoji_id:
            emoji_id=entity.custom_emoji_id; break
    label=re.sub(r"\s*<tg-emoji[^>]*>.*?</tg-emoji>\s*", " ", label, flags=re.I).strip()
    await state.update_data(welcome_current_label=label, welcome_current_emoji=emoji_id)
    await state.set_state(WelcomeSG.btn_type)
    await message.answer("اختر نوع الزر:", reply_markup=welcome_button_type_kb())

@router.callback_query(F.data.startswith("welcome_btn_type_"))
async def welcome_btn_type(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    typ=call.data.rsplit("_",1)[-1]
    if typ not in {"text","url","copy"}: await call.answer(); return
    await state.update_data(welcome_current_type=typ)
    hint={"text":"أرسل النص الذي سيظهر عند الضغط على الزر.","url":"أرسل الرابط ويجب أن يبدأ بـ https:// أو http://.","copy":"أرسل النص الذي سيتم نسخه."}[typ]
    await state.set_state(WelcomeSG.btn_value)
    await call.message.edit_text(hint, reply_markup=cancel_kb("welcome"), parse_mode="HTML")
    await call.answer()

@router.message(WelcomeSG.btn_value)
async def welcome_btn_value(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    value=(message.text or "").strip()
    if not value: await message.answer("أرسل قيمة صحيحة."); return
    data=await state.get_data()
    if data.get("welcome_current_type")=="url" and not value.startswith(("http://","https://")):
        await message.answer("الرابط يجب أن يبدأ بـ http:// أو https://"); return
    await state.update_data(welcome_current_value=value)
    await state.set_state(WelcomeSG.btn_color)
    await message.answer("اختر لون الزر:", reply_markup=welcome_button_color_kb())

@router.callback_query(F.data.startswith("welcome_btn_color_"))
async def welcome_btn_color(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    color=call.data.rsplit("_",1)[-1]
    if color not in {"danger","success","primary"}: await call.answer(); return
    data=await state.get_data()
    if not data.get("welcome_current_label") or data.get("welcome_current_value") is None:
        await call.answer("ابدأ إضافة الزر من جديد.", show_alert=True); return
    buttons=data.get("welcome_buttons",[])
    buttons.append({"label":data["welcome_current_label"],"type":data["welcome_current_type"],"value":data["welcome_current_value"],"color":color,"icon_custom_emoji_id":data.get("welcome_current_emoji","")})
    await state.update_data(welcome_buttons=buttons, welcome_current_label=None, welcome_current_value=None)
    await state.set_state(WelcomeSG.ask_more)
    await call.message.edit_text("تمت إضافة الزر. هل تريد إضافة زر آخر؟", reply_markup=_welcome_more_kb())
    await call.answer()

@router.callback_query(F.data == "welcome_btn_more")
async def welcome_btn_more(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.set_state(WelcomeSG.btn_label)
    await call.message.edit_text("أرسل اسم الزر التالي.", reply_markup=cancel_kb("welcome"))
    await call.answer()

@router.callback_query(F.data == "welcome_btn_done")
async def welcome_btn_done(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await _welcome_continue_after_buttons(call.message, state)
    await call.answer()

async def _welcome_continue_after_buttons(message: Message, state: FSMContext):
    data=await state.get_data()
    owner=await settings_owner(message.chat.id)
    await set_account_setting(owner, "welcome_buttons", json.dumps(data.get("welcome_buttons",[]), ensure_ascii=False))
    await state.set_state(WelcomeSG.ask_image)
    await message.answer("هل تريد إضافة صورة ترحيب؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نعم", callback_data="welcome_image_yes", style="success", icon_custom_emoji_id="6206479140040743133"), InlineKeyboardButton(text="لا", callback_data="welcome_image_no", style="danger", icon_custom_emoji_id="6206110936789423908")]
    ]), parse_mode="HTML")

@router.callback_query(F.data.startswith("wbtn_"))
async def welcome_button_text(call: CallbackQuery):
    try: _, owner_raw, index_raw=call.data.split("_",2); owner=int(owner_raw); index=int(index_raw)
    except Exception: await call.answer(); return
    raw=await get_account_setting(owner,"welcome_buttons") or "[]"
    try: buttons=json.loads(raw)
    except Exception: buttons=[]
    if index<0 or index>=len(buttons) or buttons[index].get("type")!="text":
        await call.answer("الزر غير متاح.",show_alert=True); return
    value=buttons[index].get("value","")
    try:
        await call.message.answer(value, business_connection_id=getattr(call.message,"business_connection_id",None), parse_mode="HTML")
    except Exception:
        await call.answer("تعذر إرسال النص.",show_alert=True); return
    await call.answer()

@router.callback_query(F.data == "welcome_buttons_manage")
async def welcome_buttons_manage(call: CallbackQuery, state: FSMContext):
    await _bted_open(call, state, "welcome", 0)

@router.callback_query(F.data == "welcome_image_yes")
async def welcome_image_yes(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WelcomeSG.set_image)
    await call.message.edit_text("أرسل صورة الترحيب الآن.", reply_markup=cancel_kb("advanced"), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "welcome_image_no")
async def welcome_image_no(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WelcomeSG.ask_mode)
    await call.message.edit_text("اختر حالة إرسال الترحيب:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="دائماً", callback_data="welcome_mode_always", style="primary"), InlineKeyboardButton(text="عند عدم الاتصال فقط", callback_data="welcome_mode_offline", style="primary")]]), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("welcome_mode_"))
async def welcome_mode_select(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    mode = call.data.removeprefix("welcome_mode_")
    await set_account_setting(await settings_owner(call.from_user.id), "welcome_mode", mode)
    await state.set_state(WelcomeSG.set_sticker)
    await call.message.edit_text("هل تريد إضافة ملصق مصاحب للترحيب؟ أرسل الملصق الآن أو اضغط إلغاء للمتابعة بدون ملصق.", reply_markup=cancel_kb("advanced"), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "welcome_settings")
async def welcome_settings(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await call.message.edit_text("<b>إعدادات رسالة الترحيب</b>\n\n<blockquote>من هنا تقدر تغيّر النص أو تحذف الصورة والملصق أو تشاهد معاينة الترحيب كما سيصل للعميل.</blockquote>", reply_markup=welcome_settings_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "welcome_preview")
async def welcome_preview(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    owner=await settings_owner(call.from_user.id)
    conn=await db(); row=await fetchone(conn, "SELECT welcome, welcome_image_file_id, welcome_sticker_file_id FROM settings WHERE owner_id=?", (owner,)); await conn.close()
    text=row["welcome"] or "لا يوجد نص ترحيب محفوظ"
    raw=await get_account_setting(owner,"welcome_buttons") or "[]"
    try: btn_data=json.loads(raw)
    except Exception: btn_data=[]
    markup=welcome_buttons_kb(btn_data,owner)
    if row["welcome_image_file_id"]:
        await call.message.answer_photo(row["welcome_image_file_id"], caption=text, reply_markup=markup, parse_mode="HTML")
    else:
        await call.message.answer(text, reply_markup=markup, parse_mode="HTML")
    if row["welcome_sticker_file_id"]:
        await call.message.answer_sticker(row["welcome_sticker_file_id"])
    await call.answer("تم إرسال المعاينة")

@router.callback_query(F.data == "welcome_sticker")
async def welcome_sticker(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WelcomeSG.set_sticker)
    await call.message.edit_text(
        "<b>إضافة ملصق للترحيب</b>\n\nأرسل الملصق العادي الآن.\n"
        "سيتم إرساله للعميل كرسالة مستقلة بعد نص الترحيب.",
        reply_markup=cancel_kb("advanced"), parse_mode="HTML"
    )
    await call.answer()

@router.message(WelcomeSG.set_sticker)
async def welcome_sticker_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if not message.sticker:
        await message.answer("أرسل ملصقاً عادياً من فضلك.")
        return
    owner = await settings_owner(message.from_user.id)
    await set_account_setting(owner, "welcome_sticker_file_id", message.sticker.file_id)
    await state.clear()
    await message.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم حفظ ملصق الترحيب بنجاح.", reply_markup=back_kb("welcome"), parse_mode="HTML")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "tracking")
async def tracking_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await state.clear(); owner=await settings_owner(call.from_user.id)
    deleted=bool(await get_account_setting(owner,"track_deleted_enabled") if await get_account_setting(owner,"track_deleted_enabled") is not None else 1)
    edited=bool(await get_account_setting(owner,"track_edited_enabled") if await get_account_setting(owner,"track_edited_enabled") is not None else 1)
    await call.message.edit_text(section_message("رصد الحذف والتعديل", "📝", "يراقب البوت رسائل العملاء التي تم تعديلها أو حذفها من شات الـ Business، ويحفظها في سجل خاص بحسابك.", "تقدر تفعّل أو تعطّل كل نوع وتعرض السجل من الأسفل."), reply_markup=tracking_kb(deleted, edited), parse_mode="HTML"); await call.answer()

async def render_tracking(call):
    owner=await settings_owner(call.from_user.id)
    d=bool(await get_account_setting(owner,"track_deleted_enabled") or 0); e=bool(await get_account_setting(owner,"track_edited_enabled") or 0)
    await call.message.edit_reply_markup(reply_markup=tracking_kb(d,e))

@router.callback_query(F.data == "tracking_toggle_deleted")
async def tracking_toggle_deleted(call: CallbackQuery):
    owner=await settings_owner(call.from_user.id); cur=await get_account_setting(owner,"track_deleted_enabled") or 0
    await set_account_setting(owner,"track_deleted_enabled",0 if cur else 1); await render_tracking(call); await call.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم تحديث إعداد رصد الحذف")

@router.callback_query(F.data == "tracking_toggle_edited")
async def tracking_toggle_edited(call: CallbackQuery):
    owner=await settings_owner(call.from_user.id); cur=await get_account_setting(owner,"track_edited_enabled") or 0
    await set_account_setting(owner,"track_edited_enabled",0 if cur else 1); await render_tracking(call); await call.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم تحديث إعداد رصد التعديل")

async def show_tracking_logs(call, event_type):
    owner=await settings_owner(call.from_user.id); conn=await db()
    rows=await conn.execute_fetchall("SELECT * FROM tracking_logs WHERE owner_id=? AND event_type=? ORDER BY id DESC LIMIT 20",(owner,event_type)); await conn.close()
    title="المحذوفة" if event_type=="deleted" else "المعدلة"
    if not rows: text=f"<b>سجل الرسائل {title}</b>\n\nلا توجد سجلات." 
    else:
        lines=[f"<b>آخر الرسائل {title}</b>"]
        for r in rows:
            body=r["old_text"] if event_type=="deleted" else f"قبل: {r['old_text']}\nبعد: {r['new_text']}"
            lines.append(f"\n<b>#{r['id']}</b>\n{tracking_identity('', '', r['chat_id'])}\n{safe_html(body[:500])}")
        text="\n".join(lines)
    await call.message.edit_text(text, reply_markup=tracking_kb(bool(await get_account_setting(owner,"track_deleted_enabled") or 0), bool(await get_account_setting(owner,"track_edited_enabled") or 0)), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "tracking_deleted")
async def tracking_deleted(call: CallbackQuery): await show_tracking_logs(call,"deleted")
@router.callback_query(F.data == "tracking_edited")
async def tracking_edited(call: CallbackQuery): await show_tracking_logs(call,"edited")
@router.callback_query(F.data == "tracking_clear")
async def tracking_clear(call: CallbackQuery):
    owner=await settings_owner(call.from_user.id)
    conn=await db(); await conn.execute("DELETE FROM tracking_logs WHERE owner_id=?",(owner,)); await conn.commit(); await conn.close()
    deleted=bool(await get_account_setting(owner,"track_deleted_enabled") or 0); edited=bool(await get_account_setting(owner,"track_edited_enabled") or 0)
    await call.message.edit_text("<b>رصد الحذف والتعديل</b>\n\n<blockquote>تم مسح سجل هذا الحساب فقط.</blockquote>", reply_markup=tracking_kb(deleted, edited), parse_mode="HTML")
    await call.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم مسح السجل بنجاح")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("هذه اللوحة للأدمنية فقط.", show_alert=True)
        return
    await state.clear()
    await edit_or_replace(call, "<b>لوحة الأدمن</b>\n\nإعدادات البوت وإدارته فقط:", admin_panel_kb())
    await call.answer()

def admin_subsection_kb(buttons):
    rows = []
    for i in range(0, len(buttons), 2):
        rows.append([
            InlineKeyboardButton(text=t, callback_data=c, style=s, icon_custom_emoji_id=e)
            for t, c, s, e in buttons[i:i + 2]
        ])
    rows.append([InlineKeyboardButton(text="رجوع للوحة الأدمن", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(F.data == "admin_force_section")
async def admin_force_section(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await state.clear()
    conn = await db()
    row = await fetchone(conn, "SELECT COUNT(*) c FROM force_channels WHERE owner_id=? AND scope='bot'", (OWNER_ID,))
    await conn.close()
    force_enabled = bool(await get_setting("bot_force_enabled") or 0)
    await call.message.edit_text(
        f"<b>قسم الاشتراك الإجباري</b>\n\nعدد القنوات: <b>{row['c'] if row else 0}</b>",
        reply_markup=admin_subsection_kb([
            (f"{'تعطيل' if force_enabled else 'تفعيل'} الاشتراك الإجباري", "admin_force_toggle", "danger" if force_enabled else "success", "6206110936789423908" if force_enabled else "6206479140040743133"),
            ("إضافة قناة", "force_add", "primary", "5778455936410588193"),
            ("عرض القنوات", "force_list", "primary", "5766902139376898645"),
            ("تعديل قناة", "force_edit_list", "primary", "5888620056551625531"),
            ("حذف قناة", "force_del_list", "danger", "6030864215139422409"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_users_section")
async def admin_users_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await call.message.edit_text(
        "<b>قسم المستخدمين والحظر</b>\n\nاختر العملية المطلوبة:",
        reply_markup=admin_subsection_kb([
            ("حظر مستخدم", "user_ban_list", "danger", "6039522349517115015"),
            ("فك حظر مستخدم", "user_unban_list", "success", "6206479140040743133"),
            ("تغيير اسم حساب فعليًا", "user_name_edit", "primary", "6039614175917903752"),
            ("الحسابات المرتبطة بالبوت", "admin_linked_accounts", "primary", "5789452774970236366"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_backup_section")
async def admin_backup_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await call.message.edit_text(
        "<b>قسم النسخ الاحتياطية</b>\n\nاختر إنشاء نسخة أو استعادة نسخة محفوظة.",
        reply_markup=admin_subsection_kb([
            ("إنشاء نسخة احتياطية", "admin_backup", "primary", "6032653721853234759"),
            ("استعادة نسخة احتياطية", "admin_restore", "success", "6206479140040743133"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_broadcast_section")
async def admin_broadcast_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await call.message.edit_text(
        "<b>قسم الإذاعة</b>\n\nاختر نوع الإذاعة:",
        reply_markup=admin_subsection_kb([
            ("إذاعة مستخدمي البوت", "admin_bot_broadcast", "primary", "6039422865189638057"),
            ("إذاعة القنوات", "admin_channel_broadcast", "primary", "6032653721853234759"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "account_messages")
async def account_messages_menu(call: CallbackQuery):
    if not await is_account_linked(call.from_user.id): return
    await call.message.edit_text("<blockquote><b>تخصيص أشكال الرسائل</b>\n\nمن هنا يمكنك تعديل رسائل حسابك فقط. استخدم الاقتباس حول العنوان واترك سطرًا فارغًا بين الفقرات إذا أردت.</blockquote>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تعديل رسالة اشتراك الحساب", callback_data="accountmsg_account_force_sub", style="primary", icon_custom_emoji_id="5260268501515377807")],
        [InlineKeyboardButton(text="تعديل رسالة الترحيب", callback_data="accountmsg_welcome", style="primary", icon_custom_emoji_id="5985478698722136468")],
        [InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ]), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("accountmsg_"))
async def account_message_start(call: CallbackQuery, state: FSMContext):
    if not await is_account_linked(call.from_user.id): return
    key=call.data.removeprefix("accountmsg_")
    await state.update_data(account_message_key=key)
    await state.set_state(AdminSG.edit_bot_message)
    owner=await settings_owner(call.from_user.id)
    current=(await get_account_setting(owner, "welcome") or await get_bot_message("welcome")) if key == "welcome" else await get_account_message(owner, key)
    await call.message.edit_text(f"<blockquote><b>تعديل رسالة الحساب</b>\n\nالرسالة الحالية:</blockquote>\n{current}\n\nأرسل النص الجديد، ويمكنك استخدام <code>&lt;blockquote&gt;</code> حول العنوان فقط وترك سطر فارغ بين الفقرات.", reply_markup=cancel_kb("advanced"), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "admin_settings_section")
async def admin_settings_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await call.message.edit_text(
        "<b>قسم إعدادات البوت</b>\n\nاختر الإعداد المطلوب:",
        reply_markup=admin_subsection_kb([
            ("الإحصائيات", "admin_stats", "primary", "5778145208411624388"),
            ("حالة البوت", "admin_status", "primary", "6039348811363520645"),
            ("فيديو لوحة التحكم", "admin_dashboard_video", "primary", "5769248574499983619"),
            ("صورة ترحيب البوت", "admin_bot_welcome_image", "primary", "6037397706505195857"),
            ("تعديل رسائل البوت", "admin_messages_section", "primary", "5985478698722136468"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_force_toggle")
async def admin_force_toggle(call: CallbackQuery):
    if call.from_user.id != OWNER_ID: return
    current = int(await get_setting("bot_force_enabled") or 0)
    await set_setting("bot_force_enabled", 0 if current else 1)
    await call.answer("تم تفعيل الاشتراك الإجباري" if not current else "تم تعطيل الاشتراك الإجباري")
    await call.message.edit_text("<b>تم تحديث حالة الاشتراك الإجباري.</b>", reply_markup=back_kb("admin_panel"), parse_mode="HTML")

def subscription_admin_kb(mode):
    toggle_text = "تفعيل الوضع المدفوع" if mode == "free" else "تفعيل الوضع المجاني"
    toggle_cb = "access_paid" if mode == "free" else "access_free"
    toggle_style = "danger" if mode == "free" else "success"
    toggle_icon = "6206110936789423908" if mode == "free" else "6206479140040743133"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_cb, style=toggle_style, icon_custom_emoji_id=toggle_icon)],
        [InlineKeyboardButton(text="إضافة اشتراك مدفوع", callback_data="sub_paid_add", style="primary", icon_custom_emoji_id="5260268501515377807"), InlineKeyboardButton(text="حذف اشتراك مدفوع", callback_data="sub_paid_delete", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="عرض الحسابات المدفوعة", callback_data="sub_paid_list", style="primary", icon_custom_emoji_id="6037397706505195857"), InlineKeyboardButton(text="إضافة فترة تجريبية", callback_data="sub_trial", style="success", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="رسالة غير المشتركين", callback_data="paidgate_menu", style="primary", icon_custom_emoji_id="6037254263187443802")],
        [InlineKeyboardButton(text="رجوع للوحة الأدمن", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")]
    ])

@router.callback_query(F.data == "admin_subscription_section")
async def admin_subscription_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID: return
    mode=await get_setting("bot_access_mode") or "free"
    mode_text = "مدفوع" if mode == "paid" else "مجاني"
    await call.message.edit_text(f"<blockquote><b>قسم الاشتراكات</b>\n\nوضع البوت الحالي: <b>{mode_text}</b>\nاختار العملية المطلوبة من الأزرار التالية.</blockquote>", reply_markup=subscription_admin_kb(mode), parse_mode="HTML")
    await call.answer()

async def set_access_mode(call, mode):
    if call.from_user.id != OWNER_ID: return
    await set_setting("bot_access_mode", mode)
    await admin_subscription_section(call)

@router.callback_query(F.data == "access_paid")
async def access_paid(call: CallbackQuery): await set_access_mode(call, "paid")
@router.callback_query(F.data == "access_free")
async def access_free(call: CallbackQuery): await set_access_mode(call, "free")

@router.callback_query(F.data.in_({"sub_paid_add", "sub_paid_delete", "sub_trial"}))
async def subscription_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID: return
    action=call.data.removeprefix("sub_")
    await state.update_data(subscription_action=action)
    await state.set_state(SubscriptionSG.user_id)
    prompt = "أرسل ID المستخدم لإضافة الاشتراك المدفوع." if action == "paid_add" else "أرسل ID المستخدم لحذف الاشتراك المدفوع." if action == "paid_delete" else "أرسل ID المستخدم لإضافة فترة تجريبية."
    await call.message.edit_text(f"<blockquote><b>{prompt}</b></blockquote>", reply_markup=cancel_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "sub_paid_list")
async def subscription_paid_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID: return
    conn=await db(); rows=await conn.execute_fetchall("SELECT user_id, expires_at FROM bot_subscriptions WHERE trial=0 ORDER BY expires_at DESC", ()); await conn.close()
    if not rows: body="لا توجد حسابات مدفوعة حالياً."
    else:
        lines=[]
        for row in rows:
            try: expiry=datetime.fromisoformat(row["expires_at"]).strftime("%Y-%m-%d %H:%M")
            except Exception: expiry=row["expires_at"]
            lines.append(f"<b>• <code>{row['user_id']}</code> — ينتهي: {expiry}</b>")
        body="\n".join(lines)
    await call.message.edit_text(f"<blockquote><b>الحسابات المدفوعة</b>\n\n{body}</blockquote>", reply_markup=back_kb("admin_subscription_section"), parse_mode="HTML")
    await call.answer()

@router.message(SubscriptionSG.user_id)
async def subscription_user_id(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    try: uid=int((message.text or '').strip())
    except: await message.answer("أرسل ID رقمي صحيح."); return
    data=await state.get_data(); action=data.get("subscription_action")
    if action == "paid_delete":
        conn=await db(); await conn.execute("DELETE FROM bot_subscriptions WHERE user_id=? AND trial=0", (uid,)); await conn.commit(); await conn.close(); await state.clear()
        await message.answer(f"<blockquote><b>تم حذف الاشتراك المدفوع للمستخدم <code>{uid}</code>.</b></blockquote>", reply_markup=back_kb("admin_subscription_section"), parse_mode="HTML"); return
    if action == "trial":
        span, label = timedelta(hours=24), "24 ساعة"
        expires=datetime.now(timezone.utc)+span
        conn=await db(); await conn.execute("INSERT INTO bot_subscriptions(user_id,expires_at,trial,created_at) VALUES(?,?,1,?) ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at,trial=1", (uid,expires.isoformat(),datetime.now(timezone.utc).isoformat())); await conn.commit(); await conn.close(); await state.clear()
        try: await message.bot.send_message(chat_id=uid, text=subscription_notice(label, expires, True), parse_mode="HTML")
        except Exception: pass
        await message.answer(f"<blockquote><b>تم تفعيل الفترة التجريبية لمدة 24 ساعة للمستخدم <code>{uid}</code>.</b></blockquote>", reply_markup=back_kb("admin_subscription_section"), parse_mode="HTML"); return
    await state.update_data(subscription_user_id=uid); await state.set_state(SubscriptionSG.duration)
    await message.answer("<blockquote><b>أرسل المدة، مثال: <code>7</code> أيام أو <code>1h</code> ساعة أو <code>1w</code> أسبوع أو <code>1m</code> شهر.</b></blockquote>", reply_markup=cancel_kb(), parse_mode="HTML")

@router.message(SubscriptionSG.duration)
async def subscription_duration_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    parsed=parse_subscription_duration(message.text)
    if not parsed:
        await message.answer("المدة غير صحيحة. استخدم رقم الأيام أو الصيغة 1h أو 1w أو 1m."); return
    span,label=parsed; data=await state.get_data(); uid=data.get("subscription_user_id"); trial=data.get("subscription_action") == "trial"
    expires=datetime.now(timezone.utc)+span
    conn=await db(); await conn.execute("INSERT INTO bot_subscriptions(user_id,expires_at,trial,created_at) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at,trial=excluded.trial", (uid,expires.isoformat(),int(trial),datetime.now(timezone.utc).isoformat())); await conn.commit(); await conn.close(); await state.clear()
    notice=subscription_notice(label, expires, trial)
    try: await message.bot.send_message(chat_id=uid, text=notice, parse_mode="HTML")
    except Exception: pass
    await message.answer(f"<blockquote><b>تم تفعيل {'الفترة التجريبية' if trial else 'الاشتراك المدفوع'} للمستخدم <code>{uid}</code>.</b></blockquote>", reply_markup=back_kb("admin_subscription_section"), parse_mode="HTML")

@router.callback_query(F.data == "admin_messages_section")
async def admin_messages_section(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذا القسم للمالك فقط.", show_alert=True)
        return
    await call.message.edit_text(
        "<b>قسم رسائل البوت</b>\n\nاختر الرسالة التي تريد تعديلها:",
        reply_markup=admin_subsection_kb([
            ("تعديل ترحيب البوت", "editmsg_welcome", "primary", "5985478698722136468"),
            ("تعديل رسالة الاشتراك", "editmsg_bot_force_sub", "primary", "5260268501515377807"),
            ("تعديل اشتراك الحساب", "editmsg_account_force_sub", "primary", "5260268501515377807"),
            ("تعديل رسالة الربط", "editmsg_link_help", "primary", "5769248574499983619"),
            ("حذف صورة الترحيب", "admin_bot_welcome_image_delete", "danger", "6039522349517115015"),
        ]), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_bot_welcome_image")
async def admin_bot_welcome_image(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await state.set_state(AdminSG.bot_welcome_image)
    await edit_or_replace(call, "<b>صورة ترحيب البوت</b>\n\nأرسل الصورة الآن، وستظهر في رسالة /start العامة للبوت.", cancel_kb())
    await call.answer()

@router.message(AdminSG.bot_welcome_image)
async def admin_bot_welcome_image_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    if not message.photo:
        await message.answer("<tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> من فضلك أرسل صورة فقط.")
        return
    await set_setting("bot_welcome_image_file_id", message.photo[-1].file_id)
    await set_setting("bot_welcome_image_type", "photo")
    await state.clear()
    await message.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم حفظ صورة ترحيب البوت العامة بنجاح.", reply_markup=back_kb("admin_settings_section"), parse_mode="HTML")

@router.callback_query(F.data == "admin_bot_welcome_image_delete")
async def admin_bot_welcome_image_delete(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await set_setting("bot_welcome_image_file_id", "")
    await set_setting("bot_welcome_image_type", "")
    await call.message.edit_text("تم حذف صورة ترحيب البوت بنجاح.", reply_markup=back_kb("admin_messages_section"), parse_mode="HTML")
    await call.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم حذف صورة ترحيب البوت بنجاح.", show_alert=True)

@router.callback_query(F.data.startswith("editmsg_"))
async def edit_bot_message_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID: return
    key=call.data[len("editmsg_"):]
    await state.update_data(bot_message_key=key); await state.set_state(AdminSG.edit_bot_message)
    current=await get_bot_message(key)
    await call.message.edit_text(f"<b>تعديل رسالة البوت</b>\n\nالرسالة الحالية:\n{current}\n\nأرسل النص الجديد. استخدم {{name}} داخل رسالة الترحيب لاسم المستخدم.", reply_markup=cancel_kb(), parse_mode="HTML"); await call.answer()

@router.message(AdminSG.edit_bot_message)
async def edit_bot_message_save(message: Message, state: FSMContext):
    data=await state.get_data()
    if message.from_user.id != OWNER_ID and not data.get("account_message_key"): return
    text=(message.html_text or message.text or "").strip()
    if not text: await message.answer("<tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> من فضلك أرسل نصاً صحيحاً."); return
    if data.get("account_message_key"):
        owner=await settings_owner(message.from_user.id); key=data.get("account_message_key")
        if key == "welcome":
            await set_account_setting(owner, "welcome", text)
        else:
            await set_account_message(owner, key, text)
        await state.clear()
        await message.answer("<blockquote><b>تم حفظ رسالة حسابك فقط بنجاح.</b></blockquote>", reply_markup=back_kb("account_messages"), parse_mode="HTML")
        return
    await set_bot_message(data.get("bot_message_key"),text); await state.clear()
    await message.answer("<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تم حفظ رسالة البوت العامة بنجاح.", reply_markup=back_kb("admin_messages_section"), parse_mode="HTML")

class StationSG(StatesGroup):
    user_id = State()
    confirm = State()

class UserModerationSG(StatesGroup):
    user_id = State()

@router.callback_query(F.data == "elzoz")
async def elzoz(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID: return
    await state.set_state(StationSG.user_id)
    await call.message.edit_text("<b>الزوز ستيشن</b>\n\nأرسل ID صاحب الحساب المرتبط.\nسيتم تنظيف بيانات البوت والرسائل التي يملك صلاحية حذفها وتعطيل الاتصالات الخاصة به. Telegram لا يسمح للبوت بالخروج من كل القنوات أو مسح كل محادثات المستخدم بالكامل.", reply_markup=cancel_kb(), parse_mode="HTML")
    await call.answer()

@router.message(StationSG.user_id)
async def elzoz_preview(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID: return
    try: uid=int((message.text or "").strip())
    except Exception:
        await message.answer("أرسل ID رقمي صحيح."); return
    conn=await db(); row=await fetchone(conn, "SELECT COUNT(*) c FROM business WHERE user_id=? AND enabled=1", (uid,)); await conn.close()
    if not row or not row["c"]:
        await message.answer("لا يوجد حساب Business مرتبط بهذا الـ ID.", reply_markup=admin_panel_kb(), parse_mode="HTML"); await state.clear(); return
    await state.update_data(station_user_id=uid); await state.set_state(StationSG.confirm)
    await message.answer(f"سيتم تنظيف بيانات البوت للحساب <code>{uid}</code> وتعطيل اتصالاته. هل تؤكد؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="نعم، تنفيذ", callback_data=f"station_execute_{uid}", style="danger", icon_custom_emoji_id="6206479140040743133")],[InlineKeyboardButton(text="إلغاء", callback_data="admin_panel", style="primary", icon_custom_emoji_id="5447647474984449520")]]), parse_mode="HTML")

@router.callback_query(F.data.startswith("station_execute_"))
async def elzoz_execute(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID: return
    uid=int(call.data.split("_")[-1]); conn=await db()
    rows=await conn.execute_fetchall("SELECT connection_id FROM business WHERE user_id=?", (uid,))
    for r in rows:
        await conn.execute("DELETE FROM customers WHERE connection_id=?", (r["connection_id"],))
        await conn.execute("DELETE FROM tracked_messages WHERE connection_id=?", (r["connection_id"],))
        await conn.execute("DELETE FROM tracking_logs WHERE connection_id=?", (r["connection_id"],))
        await conn.execute("DELETE FROM muted WHERE connection_id=?", (r["connection_id"],))
        await conn.execute("DELETE FROM violations WHERE connection_id=?", (r["connection_id"],))
        await conn.execute("UPDATE business SET enabled=0, clock_enabled=0 WHERE connection_id=?", (r["connection_id"],))
    await conn.commit(); await conn.close(); await state.clear()
    await call.message.edit_text("تم تنظيف بيانات البوت وتعطيل اتصال الحساب. لا يمكن للبوت تنفيذ الخروج من القنوات أو حذف كل محادثات Telegram بسبب حدود Bot API.", reply_markup=back_kb("admin_users_section"), parse_mode="HTML"); await call.answer("تم التنفيذ")

async def moderation_list(call: CallbackQuery, blocked: bool):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    conn=await db(); rows=await conn.execute_fetchall("SELECT user_id, first_name, username FROM bot_users WHERE blocked=? AND user_id!=? ORDER BY user_number", (1 if blocked else 0, OWNER_ID)); await conn.close()
    if not rows:
        await call.message.edit_text("لا توجد نتائج.", reply_markup=admin_panel_kb(), parse_mode="HTML"); await call.answer(); return
    prefix="user_unban" if blocked else "user_ban"
    kb=[[InlineKeyboardButton(text=f"{r['first_name'] or r['user_id']} ({r['user_id']})", callback_data=f"{prefix}_{r['user_id']}", style="success" if blocked else "danger", icon_custom_emoji_id="6206479140040743133" if blocked else "6039522349517115015")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text("اختر المستخدم:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"); await call.answer()

@router.callback_query(F.data == "user_ban_list")
async def user_ban_list(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await state.set_state(AdminSG.ban_user_id)
    await call.message.edit_text(
        "<b>حظر مستخدم من البوت</b>\n\nأرسل ID المستخدم الذي تريد حظره.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "user_unban_list")
async def user_unban_list(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await state.set_state(AdminSG.unban_user_id)
    await call.message.edit_text(
        "<b>إلغاء حظر مستخدم</b>\n\nأرسل ID المستخدم الذي تريد فك حظره.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminSG.ban_user_id)
async def ban_user_by_id(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    try:
        uid = int((message.text or "").strip())
    except (TypeError, ValueError):
        await message.answer("أرسل ID رقمي صحيح.")
        return
    if uid <= 0:
        await message.answer("أرسل ID مستخدم صحيح.")
        return
    if uid == OWNER_ID:
        await state.clear()
        await message.answer("لا يمكن حظر مالك البوت.", reply_markup=admin_panel_kb(), parse_mode="HTML")
        return
    conn = await db()
    await conn.execute(
        "INSERT INTO bot_users(user_id, first_name, username, first_seen, blocked) "
        "VALUES(?, '', '', ?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET blocked=1",
        (uid, datetime.now(timezone.utc).isoformat())
    )
    await conn.commit()
    await conn.close()
    await state.clear()
    await message.answer(
        f"تم حظر المستخدم <code>{uid}</code> من استخدام البوت.",
        reply_markup=back_kb("admin_users_section"), parse_mode="HTML"
    )

@router.message(AdminSG.unban_user_id)
async def unban_user_by_id(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    try:
        uid = int((message.text or "").strip())
    except (TypeError, ValueError):
        await message.answer("أرسل ID رقمي صحيح.")
        return
    if uid <= 0:
        await message.answer("أرسل ID مستخدم صحيح.")
        return
    conn = await db()
    cursor = await conn.execute("UPDATE bot_users SET blocked=0 WHERE user_id=?", (uid,))
    await conn.commit()
    await conn.close()
    await state.clear()
    if cursor.rowcount:
        text = f"تم إلغاء حظر المستخدم <code>{uid}</code>."
    else:
        text = f"لم أجد المستخدم <code>{uid}</code> في قائمة المحظورين."
    await message.answer(text, reply_markup=back_kb("admin_users_section"), parse_mode="HTML")

@router.callback_query(F.data.startswith("user_ban_"))
async def user_ban(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    try:
        uid = int(call.data.rsplit("_", 1)[1])
    except (TypeError, ValueError):
        await call.answer("معرّف المستخدم غير صحيح.", show_alert=True)
        return
    if uid == OWNER_ID:
        await call.answer("لا يمكن حظر مالك البوت.", show_alert=True)
        return
    conn=await db()
    cursor = await conn.execute("UPDATE bot_users SET blocked=1 WHERE user_id=? AND user_id!=?", (uid, OWNER_ID))
    await conn.commit(); await conn.close()
    await call.answer("تم حظر المستخدم." if cursor.rowcount else "المستخدم غير موجود.", show_alert=not bool(cursor.rowcount))
    await moderation_list(call, False)

@router.callback_query(F.data.startswith("user_unban_"))
async def user_unban(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    try:
        uid = int(call.data.rsplit("_", 1)[1])
    except (TypeError, ValueError):
        await call.answer("معرّف المستخدم غير صحيح.", show_alert=True)
        return
    conn=await db(); cursor = await conn.execute("UPDATE bot_users SET blocked=0 WHERE user_id=?", (uid,)); await conn.commit(); await conn.close()
    await call.answer("تم إلغاء الحظر." if cursor.rowcount else "المستخدم غير موجود.", show_alert=not bool(cursor.rowcount))
    await moderation_list(call, True)

@router.callback_query(F.data == "admin_add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.set_state(AdminSG.add_admin)
    await call.message.edit_text(
        "<b>إضافة أدمن</b>\n\nأرسل ID المستخدم.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminSG.add_admin)
async def admin_add_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    try:
        uid = int((message.text or "").strip())
    except Exception:
        await message.answer("اكتب ID رقمي صحيح.")
        return
    conn = await db()
    if uid == OWNER_ID:
        await state.clear(); await message.answer("المالك موجود بالفعل ولا يحتاج إضافة.", reply_markup=admin_panel_kb(), parse_mode="HTML"); return
    conn = await db()
    await conn.execute("INSERT INTO admins(user_id, added_at) VALUES(?, ?) ON CONFLICT(user_id) DO NOTHING", (uid, datetime.now(timezone.utc).isoformat()))
    await conn.commit(); await conn.close(); await state.clear()
    await message.answer(f"تمت إضافة الأدمن: <code>{uid}</code> ويمكنه الآن فتح لوحة الأدمن.", reply_markup=back_kb("admin_users_section"), parse_mode="HTML")

@router.callback_query(F.data == "user_name_edit")
async def user_name_edit(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    await state.set_state(AdminSG.edit_user_id)
    await call.message.edit_text(
        "<b>تغيير اسم حساب Telegram فعليًا</b>\n\n"
        "أرسل ID صاحب حساب Telegram Business المرتبط بالبوت.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminSG.edit_user_id)
async def user_name_edit_id(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    try:
        uid = int((message.text or "").strip())
    except (TypeError, ValueError):
        await message.answer("أرسل ID رقمي صحيح.")
        return
    if uid <= 0 or uid == OWNER_ID:
        await message.answer("أرسل ID مستخدم صحيح، ولا يمكن تغيير اسم مالك البوت.")
        return
    await state.update_data(edit_user_id=uid)
    await state.set_state(AdminSG.edit_user_name)
    await message.answer(
        f"تم استلام ID: <code>{uid}</code>\n\n"
        "أرسل الاسم الجديد الذي سيظهر فعليًا في حساب Telegram "
        "(من 1 إلى 64 حرفًا).",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )

@router.message(AdminSG.edit_user_name)
async def user_name_edit_save(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("أرسل الاسم الجديد كنص.")
        return
    if len(new_name) > 64:
        await message.answer("الاسم طويل جدًا. الحد الأقصى 64 حرفًا.")
        return
    data = await state.get_data()
    uid = data.get("edit_user_id")
    if not uid:
        await state.clear()
        await message.answer("انتهت العملية، ابدأ من لوحة الأدمن مرة أخرى.", reply_markup=admin_panel_kb(), parse_mode="HTML")
        return
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT connection_id FROM business WHERE user_id=? AND enabled=1 "
        "ORDER BY rowid DESC LIMIT 1",
        (uid,)
    )
    await conn.close()
    if not row:
        await state.clear()
        await message.answer(
            "لم أجد اتصال Telegram Business مفعّل لهذا الـID.\n"
            "يجب أن يكون الحساب مرتبطًا بالبوت أولًا.",
            reply_markup=admin_panel_kb(), parse_mode="HTML"
        )
        return

    try:
        current = await refresh_business_connection(message.bot, row["connection_id"])
    except Exception:
        logger.exception("Failed to refresh business connection before name update")
        current = None
    if not current or not current.is_enabled or not (current.rights and current.rights.can_edit_name):
        await state.clear()
        await message.answer(
            "لا يمكن تغيير الاسم فعليًا. الحساب غير متصل أو البوت لا يملك "
            "صلاحية تعديل اسم الحساب.",
            reply_markup=admin_panel_kb(), parse_mode="HTML"
        )
        return

    last_name = current.user.last_name or ""
    changed = await set_business_name(message.bot, row["connection_id"], new_name, last_name)
    await state.clear()
    if not changed:
        await message.answer(
            "فشل تغيير الاسم من Telegram. تأكد من صلاحيات Business وحاول مرة أخرى.",
            reply_markup=admin_panel_kb(), parse_mode="HTML"
        )
        return
    await message.answer(
        f"تم تغيير اسم حساب Telegram فعليًا للـID <code>{uid}</code> إلى: "
        f"<b>{safe_html(new_name)}</b>",
        reply_markup=back_kb("admin_users_section"), parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_list")
async def admin_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall("SELECT user_id FROM admins ORDER BY added_at")
    await conn.close()
    body = "\n".join([f"<code>{r['user_id']}</code>" for r in rows]) or "لا يوجد أدمنية."
    await call.message.edit_text(
        f"<b>الأدمنية</b>\n\nالمالك: <code>{OWNER_ID}</code>\n\n{body}",
        reply_markup=admin_panel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_del_list")
async def admin_del_list(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall("SELECT user_id FROM admins ORDER BY added_at")
    await conn.close()
    if not rows:
        await call.message.edit_text("لا يوجد أدمنية.", reply_markup=admin_panel_kb(), parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(text=str(r["user_id"]), callback_data=f"adel_{r['user_id']}", style="danger", icon_custom_emoji_id="5893192487324880883")] for r in rows]
    kb.append([InlineKeyboardButton(text="رجوع", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(
        "<b>اختر الأدمن للحذف:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML"
    )
    await call.answer()
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data.startswith("adel_"))
async def admin_del_confirm(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    uid = int(call.data.split("_")[-1])
    await call.message.edit_text(
        f"<b>تأكيد الحذف</b>\n\n<code>{uid}</code>",
        reply_markup=confirm_kb("adel", str(uid)), parse_mode="HTML"
    )
    await call.answer()
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "admin_customers")
async def admin_customers(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT chat_id, first_name, username, last_seen FROM customers "
        "WHERE connection_id IN (SELECT connection_id FROM business WHERE user_id=?) "
        "ORDER BY last_seen DESC LIMIT 50", (OWNER_ID,))
    await conn.close()
    if not rows:
        await call.message.edit_text("لا يوجد عملاء.", reply_markup=admin_panel_kb(), parse_mode="HTML")
        return
    lines = ["<b>العملاء</b>\n"]
    for r in rows:
        lines.append(
            f"<code>{r['chat_id']}</code> - {safe_html(r['first_name'])} "
            f"(@{safe_html(r['username']) or '-'})"
        )
    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_panel_kb(), parse_mode="HTML"
    )
    await call.answer()
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "admin_stats_clients")
async def admin_stats_clients(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    linked = await fetchone(conn, "SELECT COUNT(DISTINCT user_id) c FROM business WHERE enabled=1")
    bot_users_count = await fetchone(conn, "SELECT COUNT(*) c FROM bot_users WHERE user_id!=?", (OWNER_ID,))
    bot_channels_count = await fetchone(conn, "SELECT COUNT(*) c FROM bot_channels")
    admins_count = await fetchone(conn, "SELECT COUNT(*) c FROM admins")
    await conn.close()
    txt = (
        f"<b>إحصائيات {BOT_NAME}</b>\n\n"
        f"الحسابات المرتبطة: <b>{linked['c']}</b>\n"
        f"القنوات التي البوت مرفوع فيها: <b>{bot_channels_count['c']}</b>\n"
        f"مستخدمو البوت الحاليون: <b>{bot_users_count['c']}</b>\n"
        f"الأدمنية: <b>{admins_count['c']}</b>"
    )
    await call.message.edit_text(txt, reply_markup=back_kb("admin_stats"), parse_mode="HTML")
    await call.answer()
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.callback_query(F.data == "admin_backup")
async def admin_backup(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    backup_path = f"{DB}.backup_{int(datetime.now().timestamp())}"
    try:
        source = sqlite3.connect(DB)
        target = sqlite3.connect(backup_path)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        with open(backup_path, "rb") as f:
            from aiogram.types import BufferedInputFile
            doc = BufferedInputFile(
                f.read(),
                filename=f"{BOT_NAME}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
        await call.message.answer_document(
            doc,
            caption=(
                "<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> النسخة الاحتياطية جاهزة.\n"
                "تشمل العملاء، الاتصالات، الربط، الإعدادات، الردود، الكلمات والمكتومين."
            ),
            reply_markup=back_kb("admin_backup_section"),
            parse_mode="HTML"
        )
        await call.answer("تم إنشاء وإرسال النسخة الاحتياطية.")
    except Exception as e:
        logger.exception("Failed to create backup")
        await call.answer(f"فشل: {e}", show_alert=True)
    finally:
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
        except Exception:
            logger.exception("Failed to remove temporary backup")

@router.callback_query(F.data == "admin_restore")
async def admin_restore_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.set_state(AdminSG.restore_backup)
    await call.message.edit_text(
        "<b>استعادة نسخة احتياطية</b>\n\n"
        "أرسل الآن ملف النسخة الاحتياطية بصيغة <code>.db</code> أو <code>.zip</code>.\n"
        "سيتم فحصه أولاً، ولن يتم استبدال البيانات إذا كان الملف تالفاً.",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminSG.restore_backup)
async def admin_restore_save(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    if not message.document:
        await message.answer("من فضلك أرسل ملف النسخة الاحتياطية بصيغة .db أو .zip أو اضغط إلغاء.")
        return

    temp_path = f"{DB}.restore_{message.message_id}.tmp"
    extracted_path = f"{DB}.restore_{message.message_id}.extracted"
    checked_path = f"{DB}.restore_{message.message_id}.checked"
    try:
        await message.bot.download(message.document.file_id, destination=temp_path)
        restore_path = temp_path
        filename = (message.document.file_name or "").lower()
        if filename.endswith(".zip"):
            with zipfile.ZipFile(temp_path, "r") as archive:
                db_members = [
                    info for info in archive.infolist()
                    if not info.is_dir() and info.filename.lower().endswith(".db")
                ]
                if len(db_members) != 1:
                    raise ValueError("ملف ZIP يجب أن يحتوي على قاعدة بيانات DB واحدة فقط")
                with archive.open(db_members[0], "r") as source, open(extracted_path, "wb") as target_file:
                    import shutil
                    shutil.copyfileobj(source, target_file)
            restore_path = extracted_path

        source = sqlite3.connect(restore_path)
        try:
            integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
            required = {"business", "customers", "settings", "bot_users"}
            source_tables = {
                row[0] for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if integrity != "ok" or not required.issubset(source_tables):
                raise ValueError("الملف تالف أو ليس نسخة احتياطية صالحة لهذا البوت")
        finally:
            source.close()

        import shutil
        shutil.copy2(restore_path, checked_path)
        os.replace(checked_path, DB)


        await init_db()
        await state.clear()
        await message.answer(
            "<tg-emoji emoji-id='6206479140040743133'>✅</tg-emoji> تمت استعادة النسخة الاحتياطية بالكامل.\n"
            "تم مسح بيانات البوت القديمة ووضع بيانات النسخة مكانها، وسيبدأ تسجيل البيانات الجديدة داخلها.",
            reply_markup=back_kb("admin_backup_section"), parse_mode="HTML"
        )
    except Exception as e:
        logger.exception("Failed to selectively restore backup")
        await message.answer(f"<tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> لم تتم الاستعادة: {safe_html(e)}", parse_mode="HTML")
    finally:
        for path in (temp_path, extracted_path, checked_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                logger.exception("Failed to remove temporary restore file")

@router.callback_query(F.data == "admin_clear_customers")
async def admin_clear_customers(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    await conn.execute("DELETE FROM customers")
    await conn.commit()
    await conn.close()
    await call.answer("تم تصفير العملاء.", show_alert=True)

@router.callback_query(F.data == "admin_clear_muted")
async def admin_clear_muted(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    await conn.execute("DELETE FROM muted")
    await conn.commit()
    await conn.close()
    await call.answer("تم تصفير المكتومين.", show_alert=True)

@router.callback_query(F.data == "admin_clear_words")
async def admin_clear_words(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    await conn.execute("DELETE FROM banned_words WHERE owner_id=?", (OWNER_ID,))
    await conn.commit()
    await conn.close()
    await call.answer("تم تصفير الكلمات.", show_alert=True)

@router.callback_query(F.data == "admin_clear_replies")
async def admin_clear_replies(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    await conn.execute("DELETE FROM replies WHERE owner_id=?", (OWNER_ID,))
    await conn.execute("DELETE FROM reply_buttons WHERE reply_id NOT IN (SELECT id FROM replies)")
    await conn.commit()
    await conn.close()
    await call.answer("تم تصفير الردود.", show_alert=True)

@router.callback_query(F.data == "admin_status")
async def admin_status(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    conn = await db()
    row = await fetchone(conn, "SELECT enabled FROM settings WHERE owner_id=?", (OWNER_ID,))
    biz = await conn.execute_fetchall("SELECT COUNT(*) c FROM business")
    await conn.close()
    status = "مفعّل" if row["enabled"] else "متوقف"
    await call.message.edit_text(
        f"<b>حالة البوت</b>\n\n"
        f"الحالة: <b>{status}</b>\n"
        f"الاتصالات: <b>{biz[0]['c']}</b>\n"
        f"البوت يعمل بشكل طبيعي.",
        reply_markup=admin_panel_kb(), parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "admin_linked_accounts")
async def admin_linked_accounts(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT connection_id, user_id, original_name AS name, "
        "original_last_name AS last_name, enabled, can_reply, can_edit_name "
        "FROM business ORDER BY user_id, connection_id"
    )
    await conn.close()
    if not rows:
        body = "لا توجد حسابات مرتبطة محفوظة في قاعدة البيانات الحالية."
    else:
        entries = []
        for index, row in enumerate(rows, 1):
            status = "مفعّل" if row["enabled"] else "غير مفعّل"
            full_name = " ".join(
                part for part in (row["name"], row["last_name"]) if part
            ).strip() or "بدون اسم"
            entries.append(
                f"<b>الحساب رقم {index}: {safe_html(full_name)}</b>\n"
                f"الآيدي: <code>{row['user_id']}</code>\n"
                f"الحالة: <b>{status}</b>\n"
                f"صلاحية الرد: {'نعم' if row['can_reply'] else 'لا'}\n"
                f"صلاحية تعديل الاسم: {'نعم' if row['can_edit_name'] else 'لا'}"
            )
        body = "\n\n".join(entries)
        if len(body) > 3800:
            body = body[:3800] + "\n\n… القائمة طويلة، استخدم زر ملف TXT لعرض الكل."
    text = (
        f"<b>الحسابات المرتبطة بالبوت</b>\n\n"
        f"عدد الاتصالات المحفوظة: <b>{len(rows)}</b>\n\n{body}"
    )
    markup = admin_subsection_kb([
        ("تحديث القائمة", "admin_linked_accounts", "primary", "5778145208411624388"),
        ("إرسال ملف TXT", "admin_linked_accounts_txt", "success", "6032653721853234759"),
    ])
    await edit_or_replace(call, text, markup)
    await call.answer("تم عرض الحسابات المحفوظة.")

@router.callback_query(F.data == "admin_linked_accounts_txt")
async def admin_linked_accounts_txt(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return

    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT user_id, MAX(original_name) AS first_name, "
        "MAX(original_last_name) AS last_name, MAX(enabled) AS enabled, "
        "MAX(can_reply) AS can_reply, MAX(can_edit_name) AS can_edit_name, "
        "COUNT(*) AS connections "
        "FROM business GROUP BY user_id ORDER BY user_id"
    )
    await conn.close()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "تقرير الحسابات المرتبطة بالبوت",
        f"تاريخ الإنشاء: {now}",
        "ملاحظة: هذا التقرير لا يحتوي على رموز دخول أو جلسات أو محتوى رسائل.",
        "=" * 60,
        "",
    ]
    if not rows:
        lines.append("لا توجد حسابات مرتبطة حاليًا.")
    else:
        lines.extend([f"إجمالي الحسابات: {len(rows)}", ""])
        for index, row in enumerate(rows, 1):
            full_name = " ".join(
                part for part in (row["first_name"], row["last_name"]) if part
            ).strip() or "بدون اسم"
            lines.extend([
                f"الحساب رقم {index}",
                f"الاسم: {full_name}",
                f"المعرّف الرقمي: {row['user_id']}",
                f"الحالة: {'مفعّل' if row['enabled'] else 'غير مفعّل'}",
                f"صلاحية الرد: {'نعم' if row['can_reply'] else 'لا'}",
                f"صلاحية تعديل الاسم: {'نعم' if row['can_edit_name'] else 'لا'}",
                f"عدد الاتصالات: {row['connections']}",
                "-" * 40,
            ])

    document = BufferedInputFile(
        "\n".join(lines).encode("utf-8"),
        filename="linked_accounts.txt",
    )
    try:
        await call.bot.send_document(
            chat_id=OWNER_ID,
            document=document,
            caption="تقرير الحسابات المرتبطة بالبوت (بيانات غير حساسة).",
        )
        await call.answer("تم إرسال ملف الحسابات.")
    except Exception:
        logger.exception("Failed to send linked accounts TXT report")
        await call.answer("تعذر إرسال الملف، حاول مرة أخرى.", show_alert=True)

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
LIVE_BIO_CHECK_INTERVAL = timedelta(minutes=1)
LIVE_BIO_EMOJIS = {
    "islam": "5233557335397389550",
    "christian": "4902349923049014048",
}
LIVE_BIO_NAMES = {"islam": "الإسلام", "christian": "المسيحية"}


LIVE_BIO_DEFAULTS = {
    "christian": [
        "ٱلرَّبُّ رَاعِيَّ فَلَا يُعْوِزُنِي شَيْءٌ.",
        "أَيْضًا إِذَا سِرْتُ فِي وَادِي ظِلِّ ٱلْمَوْتِ لَا أَخَافُ شَرًّا، لِأَنَّكَ أَنْتَ مَعِي. عَصَاكَ وَعُكَّازُكَ هُمَا يُعَزِّيَانِنِي.",
        "اَلرَّبُّ نُورِي وَخَلَاصِي، مِمَّنْ أَخَافُ؟ ٱلرَّبُّ حِصْنُ حَيَاتِي، مِمَّنْ أَرْتَعِبُ؟",
        "ذُوقُوا وَٱنْظُرُوا مَا أَطْيَبَ ٱلرَّبَّ! طُوبَى لِلرَّجُلِ ٱلْمُتَوَكِّلِ عَلَيْهِ.",
        "قَرِيبٌ هُوَ ٱلرَّبُّ مِنَ ٱلْمُنْكَسِرِي ٱلْقُلُوبِ، وَيُخَلِّصُ ٱلْمُنْسَحِقِي ٱلرُّوحِ.",
        "وَتَلَذَّذْ بِٱلرَّبِّ فَيُعْطِيَكَ سُؤْلَ قَلْبِكَ.",
        "سَلِّمْ لِلرَّبِّ طَرِيقَكَ وَٱتَّكِلْ عَلَيْهِ وَهُوَ يُجْرِي،",
        "ٱللهُ لَنَا مَلْجَأٌ وَقُوَّةٌ. عَوْنًا فِي ٱلضِّيْقَاتِ وُجِدَ شَدِيدًا.",
        "قَلْبًا نَقِيًّا ٱخْلُقْ فِيَّ يَا ٱللهُ، وَرُوحًا مُسْتَقِيمًا جَدِّدْ فِي دَاخِلِي.",
        "أَلْقِ عَلَى ٱلرَّبِّ هَمَّكَ فَهُوَ يَعُولُكَ. لَا يَدَعُ ٱلصِّدِّيقَ يَتَزَعْزَعُ إِلَى ٱلْأَبَدِ.",
        "اَلسَّاكِنُ فِي سِتْرِ ٱلْعَلِيِّ، فِي ظِلِّ ٱلْقَدِيرِ يَبِيتُ.",
        "أَقُولُ لِلرَّبِّ: «مَلْجَإِي وَحِصْنِي. إِلَهِي فَأَتَّكِلُ عَلَيْهِ».",
        "لِأَنَّهُ يُوصِي مَلَائِكَتَهُ بِكَ لِكَيْ يَحْفَظُوكَ فِي كُلِّ طُرُقِكَ.",
        "ٱلرَّبُّ رَحِيمٌ وَرَؤُوفٌ، طَوِيلُ ٱلرُّوحِ وَكَثِيرُ ٱلرَّحْمَةِ.",
        "كَبُعْدِ ٱلْمَشْرِقِ مِنَ ٱلْمَغْرِبِ أَبْعَدَ عَنَّا مَعَاصِيَنَا.",
        "ٱلرَّبُّ لِي فَلَا أَخَافُ. مَاذَا يَصْنَعُ بِي ٱلْإِنْسَانُ؟",
        "سِرَاجٌ لِرِجْلِي كَلَامُكَ وَنُورٌ لِسَبِيلِي.",
        "أَرْفَعُ عَيْنَيَّ إِلَى ٱلْجِبَالِ، مِنْ حَيْثُ يَأْتِي عَوْنِي!",
        "مَعُونَتِي مِنْ عِنْدِ ٱلرَّبِّ، صَانِعِ ٱلسَّمَاوَاتِ وَٱلْأَرْضِ.",
        "تَوَكَّلْ عَلَى ٱلرَّبِّ بِكُلِّ قَلْبِكَ، وَعَلَى فَهْمِكَ لَا تَعْتَمِدْ.",
        "فِي كُلِّ طُرُقِكَ ٱعْرِفْهُ، وَهُوَ يُقَوِّمُ سُبُلَكَ.",
        "أَلْقِ عَلَى ٱلرَّبِّ أَعْمَالَكَ فَتُثَبَّتَ أَفْكَارُكَ.",
        "قَلْبُ ٱلْإِنْسَانِ يُفَكِّرُ فِي طَرِيقِهِ، وَٱلرَّبُّ يَهْدِي خَطْوَتَهُ.",
        "ٱلْقَلْبُ ٱلْفَرْحَانُ يُطَيِّبُ ٱلْجِسْمَ، وَٱلرُّوحُ ٱلْمُنْسَحِقَةُ تُجَفِّفُ ٱلْعَظْمَ.",
        "اِسْمُ ٱلرَّبِّ بُرْجٌ حَصِينٌ، يَرْكُضُ إِلَيْهِ ٱلصِّدِّيقُ وَيَتَمَنَّعُ.",
        "لَا تَخَفْ لِأَنِّي مَعَكَ. لَا تَتَلَفَّتْ لِأَنِّي إِلَهُكَ. قَدْ أَيَّدْتُكَ وَأَعَنْتُكَ وَعَضَدْتُكَ بِيَمِينِ بِرِّي.",
        "تَرَاءَى لِي ٱلرَّبُّ مِنْ بَعِيدٍ: «وَمَحَبَّةً أَبَدِيَّةً أَحْبَبْتُكِ، مِنْ أَجْلِ ذَلِكَ أَدَمْتُ لَكِ ٱلرَّحْمَةَ.",
        "طُوبَى لِصَانِعِي ٱلسَّلَامِ، لِأَنَّهُمْ أَبْنَاءَ ٱللهِ يُدْعَوْنَ.",
        "لَكِنِ ٱطْلُبُوا أَوَّلًا مَلَكُوتَ ٱللهِ وَبِرَّهُ، وَهَذِهِ كُلُّهَا تُزَادُ لَكُمْ.",
        "فَلَا تَهْتَمُّوا لِلْغَدِ، لِأَنَّ ٱلْغَدَ يَهْتَمُّ بِمَا لِنَفْسِهِ. يَكْفِي ٱلْيَوْمَ شَرُّهُ.",
        "«اِسْأَلُوا تُعْطَوْا. اُطْلُبُوا تَجِدُوا. اِقْرَعُوا يُفْتَحْ لَكُمْ.",
        "تَعَالَوْا إِلَيَّ يا جَمِيعَ ٱلْمُتْعَبِينَ وَٱلثَّقِيلِي ٱلْأَحْمَالِ، وَأَنَا أُرِيحُكُمْ.",
        "اِحْمِلُوا نِيرِي عَلَيْكُمْ وَتَعَلَّمُوا مِنِّي، لِأَنِّي وَدِيعٌ وَمُتَوَاضِعُ ٱلْقَلْبِ، فَتَجِدُوا رَاحَةً لِنُفُوسِكُمْ.",
        "وَعَلِّمُوهُمْ أَنْ يَحْفَظُوا جَمِيعَ مَا أَوْصَيْتُكُمْ بِهِ. وَهَا أَنَا مَعَكُمْ كُلَّ ٱلْأَيَّامِ إِلَى ٱنْقِضَاءِ ٱلدَّهْرِ». آمِينَ.",
        "لِأَنَّهُ لَيْسَ شَيْءٌ غَيْرَ مُمْكِنٍ لَدَى ٱللهِ».",
        "وَكَمَا تُرِيدُونَ أَنْ يَفْعَلَ ٱلنَّاسُ بِكُمُ ٱفْعَلُوا أَنْتُمْ أَيْضًا بِهِمْ هَكَذَا.",
        "وَأَنَا أَقُولُ لَكُمُ: ٱسْأَلُوا تُعْطَوْا، اُطْلُبُوا تَجِدُوا، اِقْرَعُوا يُفْتَحْ لَكُمْ.",
        "«لَا تَخَفْ، أَيُّهَا ٱلْقَطِيعُ ٱلصَّغِيرُ، لِأَنَّ أَبَاكُمْ قَدْ سُرَّ أَنْ يُعْطِيَكُمُ ٱلْمَلَكُوتَ.",
        "فَقَالَ لَهُمْ يَسُوعُ: «أَنَا هُوَ خُبْزُ ٱلْحَيَاةِ. مَنْ يُقْبِلْ إِلَيَّ فَلَا يَجُوعُ، وَمَنْ يُؤْمِنْ بِي فَلَا يَعْطَشُ أَبَدًا.",
        "وَتَعْرِفُونَ ٱلْحَقَّ، وَٱلْحَقُّ يُحَرِّرُكُمْ».",
        "أَنَا هُوَ ٱلرَّاعِي ٱلصَّالِحُ، وَٱلرَّاعِي ٱلصَّالِحُ يَبْذِلُ نَفْسَهُ عَنِ ٱلْخِرَافِ.",
        "وَأَنَا أُعْطِيهَا حَيَاةً أَبَدِيَّةً، وَلَنْ تَهْلِكَ إِلَى ٱلْأَبَدِ، وَلَا يَخْطَفُهَا أَحَدٌ مِنْ يَدِي.",
        "قَالَ لَهَا يَسُوعُ: «أَنَا هُوَ ٱلْقِيَامَةُ وَٱلْحَيَاةُ. مَنْ آمَنَ بِي وَلَوْ مَاتَ فَسَيَحْيَا،",
        "«لَا تَضْطَرِبْ قُلُوبُكُمْ. أَنْتُمْ تُؤْمِنُونَ بِٱللهِ فَآمِنُوا بِي.",
        "قَالَ لَهُ يَسُوعُ: «أَنَا هُوَ ٱلطَّرِيقُ وَٱلْحَقُّ وَٱلْحَيَاةُ. لَيْسَ أَحَدٌ يَأْتِي إِلَى ٱلْآبِ إِلَّا بِي.",
        "كَمَا أَحَبَّنِي ٱلْآبُ كَذَلِكَ أَحْبَبْتُكُمْ أَنَا. اُثْبُتُوا فِي مَحَبَّتِي.",
        "«هَذِهِ هِيَ وَصِيَّتِي أَنْ تُحِبُّوا بَعْضُكُمْ بَعْضًا كَمَا أَحْبَبْتُكُمْ.",
        "وَهَذِهِ هِيَ ٱلْحَيَاةُ ٱلْأَبَدِيَّةُ: أَنْ يَعْرِفُوكَ أَنْتَ ٱلْإِلَهَ ٱلْحَقِيقِيَّ وَحْدَكَ وَيَسُوعَ ٱلْمَسِيحَ ٱلَّذِي أَرْسَلْتَهُ.",
        "فَإِذْ قَدْ تَبَرَّرْنَا بِٱلْإِيمَانِ لَنَا سَلَامٌ مَعَ ٱللهِ بِرَبِّنَا يَسُوعَ ٱلْمَسِيحِ،",
        "وَٱلرَّجَاءُ لَا يُخْزِي، لِأَنَّ مَحَبَّةَ ٱللهِ قَدِ ٱنْسَكَبَتْ فِي قُلُوبِنَا بِٱلرُّوحِ ٱلْقُدُسِ ٱلْمُعْطَى لَنَا.",
        "وَلَكِنَّ ٱللهَ بَيَّنَ مَحَبَّتَهُ لَنَا، لِأَنَّهُ وَنَحْنُ بَعْدُ خُطَاةٌ مَاتَ ٱلْمَسِيحُ لِأَجْلِنَا.",
        "فَمَاذَا نَقُولُ لِهَذَا؟ إِنْ كَانَ ٱللهُ مَعَنَا، فَمَنْ عَلَيْنَا؟",
        "وَلَا عُلْوَ وَلَا عُمْقَ، وَلَا خَلِيقَةَ أُخْرَى، تَقْدِرُ أَنْ تَفْصِلَنَا عَنْ مَحَبَّةِ ٱللهِ ٱلَّتِي فِي ٱلْمَسِيحِ يَسُوعَ رَبِّنَا.",
        "فَرِحِينَ فِي ٱلرَّجَاءِ، صَابِرِينَ فِي ٱلضِّيْقِ، مُواظِبِينَ عَلَى ٱلصَّلَاةِ،",
        "وَلْيَمْلَأْكُمْ إِلَهُ ٱلرَّجَاءِ كُلَّ سُرُورٍ وَسَلَامٍ فِي ٱلْإِيمَانِ، لِتَزْدَادُوا فِي ٱلرَّجَاءِ بِقُوَّةِ ٱلرُّوحِ ٱلْقُدُسِ.",
        "ٱلْمَحَبَّةُ تَتَأَنَّى وَتَرْفُقُ. ٱلْمَحَبَّةُ لَا تَحْسِدُ. ٱلْمَحَبَّةُ لَا تَتَفَاخَرُ، وَلَا تَنْتَفِخُ،",
        "وَلَا تُقَبِّحُ، وَلَا تَطْلُبُ مَا لِنَفْسِهَا، وَلَا تَحْتَدُّ، وَلَا تَظُنُّ ٱلسُّؤَ،",
        "وَتَحْتَمِلُ كُلَّ شَيْءٍ، وَتُصَدِّقُ كُلَّ شَيْءٍ، وَتَرْجُو كُلَّ شَيْءٍ، وَتَصْبِرُ عَلَى كُلِّ شَيْءٍ.",
        "أَمَّا ٱلْآنَ فَيَثْبُتُ: ٱلْإِيمَانُ وَٱلرَّجَاءُ وَٱلْمَحَبَّةُ، هَذِهِ ٱلثَّلَاثَةُ وَلَكِنَّ أَعْظَمَهُنَّ ٱلْمَحَبَّةُ.",
        "لِتَصِرْ كُلُّ أُمُورِكُمْ فِي مَحَبَّةٍ.",
        "لِأَنَّنَا بِٱلْإِيمَانِ نَسْلُكُ لَا بِٱلْعِيَانِ.",
        "لِأَنَّكُمْ بِٱلنِّعْمَةِ مُخَلَّصُونَ، بِٱلْإِيمَانِ، وَذَلِكَ لَيْسَ مِنْكُمْ. هُوَ عَطِيَّةُ ٱللهِ.",
        "وَكُونُوا لُطَفَاءَ بَعْضُكُمْ نَحْوَ بَعْضٍ، شَفُوقِينَ، مُتَسَامِحِينَ كَمَا سَامَحَكُمُ ٱللهُ أَيْضًا فِي ٱلْمَسِيحِ.",
        "اِفْرَحُوا فِي ٱلرَّبِّ كُلَّ حِينٍ، وَأَقُولُ أَيْضًا: ٱفْرَحُوا.",
        "لَا تَهْتَمُّوا بِشَيْءٍ، بَلْ فِي كُلِّ شَيْءٍ بِٱلصَّلَاةِ وَٱلدُّعَاءِ مَعَ ٱلشُّكْرِ، لِتُعْلَمْ طِلْبَاتُكُمْ لَدَى ٱللهِ.",
        "وَسَلَامُ ٱللهِ ٱلَّذِي يَفُوقُ كُلَّ عَقْلٍ، يَحْفَظُ قُلُوبَكُمْ وَأَفْكَارَكُمْ فِي ٱلْمَسِيحِ يَسُوعَ.",
        "أَسْتَطِيعُ كُلَّ شَيْءٍ فِي ٱلْمَسِيحِ ٱلَّذِي يُقَوِّينِي.",
        "فَٱلْبَسُوا كَمُخْتَارِي ٱللهِ ٱلْقِدِّيسِينَ ٱلْمَحْبُوبِينَ أَحْشَاءَ رَأْفَاتٍ، وَلُطْفًا، وَتَوَاضُعًا، وَوَدَاعَةً، وَطُولَ أَنَاةٍ،",
        "وَعَلَى جَمِيعِ هَذِهِ ٱلْبَسُوا ٱلْمَحَبَّةَ ٱلَّتِي هِيَ رِبَاطُ ٱلْكَمَالِ.",
        "وَلْيَمْلِكْ فِي قُلُوبِكُمْ سَلَامُ ٱللهِ ٱلَّذِي إِلَيْهِ دُعِيتُمْ فِي جَسَدٍ وَاحِدٍ، وَكُونُوا شَاكِرِينَ.",
        "ٱفْرَحُوا كُلَّ حِينٍ.",
        "صَلُّوا بِلَا ٱنْقِطَاعٍ.",
        "ٱشْكُرُوا فِي كُلِّ شَيْءٍ، لِأَنَّ هَذِهِ هِيَ مَشِيئَةُ ٱللهِ فِي ٱلْمَسِيحِ يَسُوعَ مِنْ جِهَتِكُمْ.",
        "لِأَنَّ ٱللهَ لَمْ يُعْطِنَا رُوحَ ٱلْفَشَلِ، بَلْ رُوحَ ٱلْقُوَّةِ وَٱلْمَحَبَّةِ وَٱلنُّصْحِ.",
        "فَلْنَتَقَدَّمْ بِثِقَةٍ إِلَى عَرْشِ ٱلنِّعْمَةِ لِكَيْ نَنَالَ رَحْمَةً وَنَجِدَ نِعْمَةً عَوْنًا فِي حِينِهِ.",
        "مُلْقِينَ كُلَّ هَمِّكُمْ عَلَيْهِ، لِأَنَّهُ هُوَ يَعْتَنِي بِكُمْ.",
        "وَمَنْ لَا يُحِبُّ لَمْ يَعْرِفِ ٱللهَ، لِأَنَّ ٱللهَ مَحَبَّةٌ.",
        "لِأَنَّهُ مِثْلُ ٱرْتِفَاعِ ٱلسَّمَاوَاتِ فَوْقَ ٱلْأَرْضِ قَوِيَتْ رَحْمَتُهُ عَلَى خَائِفِيهِ.",
        "اَلرَّبُّ حَنَّانٌ وَرَحِيمٌ، طَوِيلُ ٱلرُّوحِ وَكَثِيرُ ٱلرَّحْمَةِ.",
        "يَشْفِي ٱلْمُنْكَسِرِي ٱلْقُلُوبِ، وَيَجْبُرُ كَسْرَهُمْ.",
        "هَذَا هُوَ ٱلْيَوْمُ ٱلَّذِي صَنَعُهُ ٱلرَّبُّ، نَبْتَهِجُ وَنَفْرَحُ فِيهِ.",
        "كَثِيرَةٌ هِيَ بَلَايَا ٱلصِّدِّيقِ، وَمِنْ جَمِيعِهَا يُنَجِّيهِ ٱلرَّبُّ.",
        "رَبِّ ٱلْوَلَدَ فِي طَرِيقِهِ، فَمَتَى شَاخَ أَيْضًا لَا يَحِيدُ عَنْهُ.",
        "اَلْعِزُّ وَٱلْبَهَاءُ لِبَاسُهَا، وَتَضْحَكُ عَلَى ٱلزَّمَنِ ٱلْآتِي.",
        "هُوَذَا ٱللهُ خَلَاصِي فَأَطْمَئِنُّ وَلَا أَرْتَعِبُ، لِأَنَّ يَاهَ يَهْوَهَ قُوَّتِي وَتَرْنِيمَتِي وَقَدْ صَارَ لِي خَلَاصًا».",
        "ذُو ٱلرَّأْيِ ٱلْمُمَكَّنِ تَحْفَظُهُ سَالِمًا سَالِمًا، لِأَنَّهُ عَلَيْكَ مُتَوَكِّلٌ.",
        "تَوَكَّلُوا عَلَى ٱلرَّبِّ إِلَى ٱلْأَبَدِ، لِأَنَّ فِي يَاهَ ٱلرَّبِّ صَخْرَ ٱلدُّهُورِ.",
        "يُعْطِي ٱلْمُعْيِيَ قُدْرَةً، وَلِعَدِيمِ ٱلْقُوَّةِ يُكَثِّرُ شِدَّةً.",
        "لِأَنِّي أَنَا ٱلرَّبُّ إِلَهُكَ ٱلْمُمْسِكُ بِيَمِينِكَ، ٱلْقَائِلُ لَكَ: لَا تَخَفْ. أَنَا أُعِينُكَ.",
        "اُدْعُنِي فَأُجِيبَكَ وَأُخْبِرَكَ بِعَظَائِمَ وَعَوَائِصَ لَمْ تَعْرِفْهَا.",
        "إِنَّهُ مِنْ إِحْسَانَاتِ ٱلرَّبِّ أَنَّنَا لَمْ نَفْنَ، لِأَنَّ مَرَاحِمَهُ لَا تَزُولُ.",
        "«طُوبَى لِلْمَسَاكِينِ بِٱلرُّوحِ، لِأَنَّ لَهُمْ مَلَكُوتَ ٱلسَّمَاوَاتِ.",
        "طُوبَى لِلْحَزَانَى، لِأَنَّهُمْ يَتَعَزَّوْنَ.",
        "طُوبَى لِلْجِيَاعِ وَٱلْعِطَاشِ إِلَى ٱلْبِرِّ، لِأَنَّهُمْ يُشْبَعُونَ.",
        "طُوبَى لِلْأَنْقِيَاءِ ٱلْقَلْبِ، لِأَنَّهُمْ يُعَايِنُونَ ٱللهَ.",
        "فَلْيُضِئْ نُورُكُمْ هَكَذَا قُدَّامَ ٱلنَّاسِ، لِكَيْ يَرَوْا أَعْمَالَكُمُ ٱلْحَسَنَةَ، وَيُمَجِّدُوا أَبَاكُمُ ٱلَّذِي فِي ٱلسَّمَاوَاتِ.",
        "فَنَظَرَ إِلَيْهِمْ يَسُوعُ وَقَالَ لَهُمْ: «هَذَا عِنْدَ ٱلنَّاسِ غَيْرُ مُسْتَطَاعٍ، وَلَكِنْ عِنْدَ ٱللهِ كُلُّ شَيْءٍ مُسْتَطَاعٌ».",
        "فَقَالَ: «غَيْرُ ٱلْمُسْتَطَاعِ عِنْدَ ٱلنَّاسِ مُسْتَطَاعٌ عِنْدَ ٱللهِ».",
        "فَقَالَ يَسُوعُ لِلْيَهُودِ ٱلَّذِينَ آمَنُوا بِهِ: «إِنَّكُمْ إِنْ ثَبَتُّمْ فِي كَلَامِي فَبِالْحَقِيقَةِ تَكُونُونَ تَلَامِيذِي،",
        "وَمَهْمَا سَأَلْتُمْ بِٱسْمِي فَذَلِكَ أَفْعَلُهُ لِيَتَمَجَّدَ ٱلْآبُ بِٱلِٱبْنِ."
    ],
    "islam": [
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ رِضَاكَ وَالْجَنَّةَ، وَأَعُوذُ بِكَ مِنْ سَخَطِكَ وَالنَّارِ.",
        "اللَّهُمَّ بَارِكْ لِي فِي رِزْقِي، وَوَسِّعْ عَلَيَّ مِنْ فَضْلِكَ.",
        "اللَّهُمَّ اغْفِرْ لِي ذُنُوبِي، وَارْحَمْنِي، وَاهْدِنِي إِلَى صِرَاطِكَ الْمُسْتَقِيمِ.",
        "اللَّهُمَّ اغْفِرْ لِوَالِدَيَّ، وَارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا.",
        "اللَّهُمَّ عَافِنِي فِي بَدَنِي، وَسَمْعِي، وَبَصَرِي، وَاجْعَلْنِي مِنَ الشَّاكِرِينَ.",
        "اللَّهُمَّ اهْدِ قَلْبِي، وَسَدِّدْ لِسَانِي، وَأَصْلِحْ لِي شَأْنِي كُلَّهُ.",
        "اللَّهُمَّ ارْزُقْنِي صَبْرًا جَمِيلًا، وَفَرَجًا قَرِيبًا، وَيَقِينًا صَادِقًا.",
        "اللَّهُمَّ أَذْهِبْ عَنِّي الْهَمَّ وَالْحَزَنَ، وَأَبْدِلْنِي سَكِينَةً وَطُمَأْنِينَةً.",
        "اللَّهُمَّ اجْعَلْ قَلْبِي مُطْمَئِنًّا بِذِكْرِكَ، وَعَامِرًا بِحُبِّكَ وَطَاعَتِكَ.",
        "اللَّهُمَّ تَقَبَّلْ عَمَلِي، وَأَخْلِصْ نِيَّتِي، وَاجْعَلْهُ خَالِصًا لِوَجْهِكَ الْكَرِيمِ.",
        "اللَّهُمَّ ارْزُقْنِي حَلَالًا طَيِّبًا، وَقَنِّعْنِي بِمَا رَزَقْتَنِي، وَبَارِكْ لِي فِيهِ.",
        "اللَّهُمَّ اكْفِنِي بِحَلَالِكَ عَنْ حَرَامِكَ، وَأَغْنِنِي بِفَضْلِكَ عَمَّنْ سِوَاكَ.",
        "اللَّهُمَّ اجْعَلْ لِي مِنْ كُلِّ هَمٍّ فَرَجًا، وَمِنْ كُلِّ ضِيقٍ مَخْرَجًا، وَارْزُقْنِي مِنْ حَيْثُ لَا أَحْتَسِبُ.",
        "اللَّهُمَّ لَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ، وَتَوَلَّنِي بِلُطْفِكَ وَرَحْمَتِكَ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ، وَالسَّلَامَةَ فِي الدِّينِ وَالدُّنْيَا وَالْآخِرَةِ.",
        "اللَّهُمَّ نَقِّ قَلْبِي مِنَ الرِّيَاءِ، وَعَمَلِي مِنَ الْخَطَأِ، وَلِسَانِي مِنَ الْكَذِبِ.",
        "اللَّهُمَّ زَيِّنْ قَلْبِي بِالْإِيمَانِ، وَحَبِّبْ إِلَيَّ الطَّاعَةَ، وَكَرِّهْ إِلَيَّ الْمَعْصِيَةَ.",
        "اللَّهُمَّ اجْعَلْنِي مِنَ التَّوَّابِينَ، وَاجْعَلْنِي مِنَ الْمُتَطَهِّرِينَ.",
        "اللَّهُمَّ ارْزُقْنِي لِسَانًا ذَاكِرًا، وَقَلْبًا خَاشِعًا، وَعَمَلًا صَالِحًا مُتَقَبَّلًا.",
        "اللَّهُمَّ ثَبِّتْنِي عَلَى الْحَقِّ، وَاصْرِفْ عَنِّي الْفِتَنَ مَا ظَهَرَ مِنْهَا وَمَا بَطَنَ.",
        "اللَّهُمَّ أَصْلِحْ لِي دِينِي وَدُنْيَايَ، وَاجْعَلِ الْآخِرَةَ خَيْرًا لِي وَمَآبًا.",
        "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا.",
        "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ، وَيَسِّرْ لِي أَبْوَابَ الْخَيْرِ.",
        "اللَّهُمَّ بَارِكْ لِي فِي وَقْتِي، وَأَعِنِّي عَلَى اسْتِغْلَالِهِ فِيمَا يُرْضِيكَ.",
        "اللَّهُمَّ اجْعَلْ غَدِي أَفْضَلَ مِنْ يَوْمِي، وَاجْعَلْ خَيْرَ أَيَّامِي يَوْمَ أَلْقَاكَ.",
        "اللَّهُمَّ احْفَظْنِي وَأَهْلِي مِنْ كُلِّ سُوءٍ، وَأَحِطْنَا بِرِعَايَتِكَ وَأَمَانِكَ.",
        "اللَّهُمَّ أَلِّفْ بَيْنَ قُلُوبِنَا، وَأَصْلِحْ ذَاتَ بَيْنِنَا، وَاهْدِنَا سُبُلَ السَّلَامِ.",
        "اللَّهُمَّ ارْزُقْنِي حُسْنَ الْخُلُقِ، وَطِيبَ الْكَلَامِ، وَسَلَامَةَ الصَّدْرِ.",
        "اللَّهُمَّ اجْعَلْنِي سَبَبًا لِلْخَيْرِ، وَاصْرِفْ بِي الشَّرَّ، وَانْفَعْ بِي عِبَادَكَ.",
        "اللَّهُمَّ اغْفِرْ لِلْمُؤْمِنِينَ وَالْمُؤْمِنَاتِ، وَارْحَمْ أَحْيَاءَهُمْ وَأَمْوَاتَهُمْ.",
        "اللَّهُمَّ ارْحَمْ ضَعْفِي، وَاجْبُرْ كَسْرِي، وَآمِنْ خَوْفِي، وَفَرِّجْ كَرْبِي.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ رَحْمَةً تَغْنِينِي بِهَا عَنْ رَحْمَةِ مَنْ سِوَاكَ.",
        "اللَّهُمَّ اجْعَلْنِي رَاضِيًا بِقَضَائِكَ، مُطْمَئِنًّا بِحُكْمِكَ، حَامِدًا لِنِعْمَتِكَ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ هَذَا الْيَوْمِ، وَأَعُوذُ بِكَ مِنْ شَرِّهِ وَشَرِّ مَا بَعْدَهُ.",
        "اللَّهُمَّ اجْعَلْنِي مِمَّنْ يَسْتَمِعُونَ الْقَوْلَ فَيَتَّبِعُونَ أَحْسَنَهُ.",
        "اللَّهُمَّ بَصِّرْنِي بِعُيُوبِي، وَأَلْهِمْنِي إِصْلَاحَهَا، وَلَا تَشْغَلْنِي بِعُيُوبِ النَّاسِ.",
        "اللَّهُمَّ طَهِّرْ قَلْبِي مِنَ الْحِقْدِ وَالْحَسَدِ، وَامْلَأْهُ رَحْمَةً وَمَحَبَّةً.",
        "اللَّهُمَّ اجْعَلْنِي لَيِّنًا فِي الْحَقِّ، حَكِيمًا فِي قَوْلِي، عَادِلًا فِي حُكْمِي.",
        "اللَّهُمَّ قَوِّ إِيمَانِي، وَزِدْنِي هُدًى، وَاجْعَلْنِي مِنْ عِبَادِكَ الصَّالِحِينَ.",
        "اللَّهُمَّ أَحْسِنْ خَاتِمَتِي، وَاجْعَلْ آخِرَ كَلَامِي مِنَ الدُّنْيَا شَهَادَةَ الْحَقِّ.",
        "اللَّهُمَّ أَدْخِلْنِي الْجَنَّةَ بِرَحْمَتِكَ، وَنَجِّنِي مِنَ النَّارِ بِعَفْوِكَ.",
        "اللَّهُمَّ اجْعَلْ قَبْرِي رَوْضَةً مِنْ رِيَاضِ الْجَنَّةِ، وَنَوِّرْهُ بِنُورِكَ.",
        "اللَّهُمَّ يَسِّرْ لِي أَمْرِي، وَاشْرَحْ لِي صَدْرِي، وَاحْلُلْ عُقْدَةً مِنْ لِسَانِي.",
        "اللَّهُمَّ أَلْهِمْنِي رُشْدِي، وَقِنِي شَرَّ نَفْسِي، وَوَفِّقْنِي لِمَا تُحِبُّ وَتَرْضَى.",
        "اللَّهُمَّ اجْعَلْنِي مِنَ الْمُحْسِنِينَ، وَأَحْسِنْ إِلَيَّ كَمَا أَحْسَنْتَ إِلَى عِبَادِكَ.",
        "اللَّهُمَّ ارْزُقْنِي صِدْقَ التَّوَكُّلِ عَلَيْكَ، وَحُسْنَ الظَّنِّ بِكَ، وَدَوَامَ الِافْتِقَارِ إِلَيْكَ.",
        "اللَّهُمَّ لَا تَحْرِمْنِي خَيْرَ مَا عِنْدَكَ بِشَرِّ مَا عِنْدِي، وَاغْفِرْ لِي وَتُبْ عَلَيَّ.",
        "اللَّهُمَّ اجْعَلْنِي مِنَ الصَّابِرِينَ عِنْدَ الْبَلَاءِ، وَالشَّاكِرِينَ عِنْدَ الرَّخَاءِ.",
        "اللَّهُمَّ بَدِّلْ خَوْفِي أَمْنًا، وَحُزْنِي فَرَحًا، وَضِيقِي سَعَةً مِنْ فَضْلِكَ.",
        "اللَّهُمَّ أَنْزِلْ عَلَى قَلْبِي سَكِينَةً، وَعَلَى رُوحِي طُمَأْنِينَةً، وَعَلَى أَيَّامِي بَرَكَةً.",
        "اللَّهُمَّ ارْزُقْنِي صُحْبَةً صَالِحَةً تُذَكِّرُنِي بِكَ، وَتُعِينُنِي عَلَى طَاعَتِكَ.",
        "اللَّهُمَّ اجْعَلْ بَيْتِي بَيْتَ مَوَدَّةٍ وَرَحْمَةٍ وَذِكْرٍ، وَأَبْعِدْ عَنَّا الشِّقَاقَ.",
        "اللَّهُمَّ بَارِكْ لِي فِي أَهْلِي وَأَوْلَادِي، وَاحْفَظْهُمْ مِنْ كُلِّ مَكْرُوهٍ.",
        "اللَّهُمَّ ارْزُقْنِي بَرَّ وَالِدَيَّ، وَاجْزِهِمَا عَنِّي خَيْرَ الْجَزَاءِ.",
        "اللَّهُمَّ اشْفِ مَرْضَانَا، وَارْحَمْ مَوْتَانَا، وَعَافِ مُبْتَلَانَا، وَفُكَّ أَسْرَ مَأْسُورِنَا.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ شِفَاءً لَا يُغَادِرُ سَقَمًا، وَعَافِيَةً تَامَّةً وَدَائِمَةً.",
        "اللَّهُمَّ كُنْ لِلْمَظْلُومِينَ نَاصِرًا، وَلِلْمَكْرُوبِينَ فَرَجًا، وَلِلْمُحْتَاجِينَ عَوْنًا.",
        "اللَّهُمَّ اجْمَعْ كَلِمَةَ الْمُسْلِمِينَ عَلَى الْحَقِّ، وَأَصْلِحْ أَحْوَالَهُمْ وَارْزُقْهُمُ السَّلَامَ.",
        "اللَّهُمَّ احْفَظْ بِلَادَنَا وَبِلَادَ الْمُسْلِمِينَ، وَادْفَعْ عَنَّا الْفِتَنَ وَالْحُرُوبَ.",
        "اللَّهُمَّ أَطْعِمْ جَائِعَنَا، وَاكْسُ عَارِيَنَا، وَارْحَمْ فَقِيرَنَا، وَأَغْنِ مُحْتَاجَنَا.",
        "اللَّهُمَّ اجْعَلْنِي مِمَّنْ يَعْفُونَ عَمَّنْ ظَلَمَهُمْ، وَيَصِلُونَ مَنْ قَطَعَهُمْ، وَيُحْسِنُونَ إِلَى مَنْ أَسَاءَ.",
        "اللَّهُمَّ أَعِذْنِي مِنْ شَرِّ نَفْسِي، وَمِنْ شَرِّ الشَّيْطَانِ، وَمِنْ كُلِّ سُوءٍ.",
        "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ، وَالْعَجْزِ وَالْكَسَلِ، وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ.",
        "اللَّهُمَّ أَعِذْنِي مِنْ قَلْبٍ لَا يَخْشَعُ، وَعَيْنٍ لَا تَدْمَعُ، وَدُعَاءٍ لَا يُسْمَعُ.",
        "اللَّهُمَّ احْفَظْنِي مِنْ فِتْنَةِ الدُّنْيَا، وَزَيِّنْ لِي طَاعَتَكَ، وَهَوِّنْ عَلَيَّ مَشَقَّةَ الْخَيْرِ.",
        "اللَّهُمَّ اجْعَلْنِي مِنَ الْمُتَحَابِّينَ فِيكَ، وَالْمُتَنَاصِحِينَ لِوَجْهِكَ، وَالْمُتَعَاوِنِينَ عَلَى الْبِرِّ.",
        "اللَّهُمَّ أَصْلِحْ لِي مَا بَيْنِي وَبَيْنَكَ، وَأَصْلِحْ لِي مَا بَيْنِي وَبَيْنَ النَّاسِ.",
        "اللَّهُمَّ ارْزُقْنِي حِكْمَةً فِي قَوْلِي، وَبَصِيرَةً فِي أَمْرِي، وَإِخْلَاصًا فِي عَمَلِي.",
        "اللَّهُمَّ اجْعَلْنِي شَاكِرًا لِنِعَمِكَ، حَافِظًا لِحُدُودِكَ، مُقْبِلًا عَلَى طَاعَتِكَ.",
        "اللَّهُمَّ اكْتُبْ لِي الْخَيْرَ حَيْثُ كَانَ، ثُمَّ ارْضِنِي بِهِ وَبَارِكْ لِي فِيهِ.",
        "اللَّهُمَّ لَا تَجْعَلِ الدُّنْيَا أَكْبَرَ هَمِّنَا، وَلَا مَبْلَغَ عِلْمِنَا، وَاجْعَلِ الْآخِرَةَ هَمَّنَا.",
        "اللَّهُمَّ اجْعَلْنِي أَكْثَرَ ذِكْرًا لَكَ، وَأَكْثَرَ شُكْرًا لَكَ، وَأَحْسَنَ عِبَادَةً لَكَ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ الثَّبَاتَ فِي الْأَمْرِ، وَالْعَزِيمَةَ عَلَى الرُّشْدِ، وَحُسْنَ الْخَاتِمَةِ.",
        "اللَّهُمَّ ارْزُقْنِي تَوْبَةً نَصُوحًا، وَقَلْبًا مُنِيبًا، وَعَمَلًا يَرْفَعُ دَرَجَتِي عِنْدَكَ.",
        "اللَّهُمَّ اغْسِلْ خَطَايَايَ بِالْمَاءِ وَالثَّلْجِ وَالْبَرَدِ، وَنَقِّنِي مِنَ الذُّنُوبِ.",
        "اللَّهُمَّ أَعِنِّي عَلَى غَضِّ بَصَرِي، وَحِفْظِ لِسَانِي، وَصِيَانَةِ قَلْبِي.",
        "اللَّهُمَّ اجْعَلْنِي مِفْتَاحًا لِلْخَيْرِ، مِغْلَاقًا لِلشَّرِّ، مُبَارَكًا أَيْنَمَا كُنْتُ.",
        "اللَّهُمَّ اجْعَلْ مَا أَخْفَيْتُهُ مِنَ الْعَمَلِ أَصْلَحَ مِمَّا أَظْهَرْتُ، وَاغْفِرْ تَقْصِيرِي.",
        "اللَّهُمَّ بَارِكْ فِي سَعْيِي، وَوَفِّقْنِي فِي عَمَلِي، وَافْتَحْ لِي أَبْوَابَ الرِّزْقِ الْحَلَالِ.",
        "اللَّهُمَّ أَلْهِمْنِي الْقَوْلَ السَّدِيدَ، وَالْعَمَلَ الرَّشِيدَ، وَالْقَصْدَ الْحَمِيدَ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ رِزْقًا وَاسِعًا، وَقَلْبًا قَانِعًا، وَعَيْشًا هَنِيئًا.",
        "اللَّهُمَّ صَرِّفْ عَنِّي كُلَّ مَا يُبْعِدُنِي عَنْكَ، وَقَرِّبْنِي إِلَيْكَ بِمَا تُحِبُّ.",
        "اللَّهُمَّ اجْعَلْنِي أَرْجُو رَحْمَتَكَ، وَأَخْشَى عَذَابَكَ، وَأُحْسِنُ الظَّنَّ بِكَ.",
        "اللَّهُمَّ أَكْرِمْنِي بِحُبِّكَ، وَحُبِّ مَنْ يُحِبُّكَ، وَحُبِّ عَمَلٍ يُقَرِّبُنِي إِلَى حُبِّكَ.",
        "اللَّهُمَّ اجْعَلْنِي مِنْ أَهْلِ الْقُرْآنِ، وَارْزُقْنِي تِلَاوَتَهُ وَتَدَبُّرَهُ وَالْعَمَلَ بِهِ.",
        "اللَّهُمَّ نَوِّرْ قَلْبِي بِالْإِيمَانِ، وَزَيِّنْ حَيَاتِي بِالْقُرْآنِ، وَاجْعَلْهُ شَفِيعًا لِي.",
        "اللَّهُمَّ أَعِذْنِي مِنْ عَذَابِ الْقَبْرِ، وَمِنْ فِتْنَةِ الْمَحْيَا وَالْمَمَاتِ، وَمِنْ فِتْنَةِ الْمَسِيحِ الدَّجَّالِ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى، وَالْعَفَافَ وَالْغِنَى.",
        "اللَّهُمَّ اهْدِنِي وَسَدِّدْنِي، وَاجْعَلْ هِدَايَتِي سَبَبًا لِصَلَاحِ أَمْرِي.",
        "اللَّهُمَّ ارْزُقْنِي قَلْبًا سَلِيمًا، وَصَدْرًا وَاسِعًا، وَنَفْسًا رَاضِيَةً.",
        "اللَّهُمَّ اجْعَلْنِي أَمِينًا فِي عَمَلِي، صَادِقًا فِي وَعْدِي، وَفِيًّا فِي عَهْدِي.",
        "اللَّهُمَّ أَصْلِحْ أَحْوَالَنَا، وَاجْمَعْنَا عَلَى الْمَوَدَّةِ، وَاصْرِفْ عَنَّا الْخُصُومَةَ وَالْفُرْقَةَ.",
        "اللَّهُمَّ اجْعَلْنِي عَوْنًا لِمَنْ احْتَاجَ إِلَيَّ، وَرَحْمَةً لِمَنْ ضَعُفَ، وَنُورًا لِمَنْ اهْتَدَى.",
        "اللَّهُمَّ ارْزُقْنِي قُوَّةً عَلَى الطَّاعَةِ، وَصَبْرًا عَنِ الْمَعْصِيَةِ، وَشُكْرًا عِنْدَ النِّعْمَةِ.",
        "اللَّهُمَّ اجْعَلْنِي أُحِبُّ لِلنَّاسِ مَا أُحِبُّ لِنَفْسِي، وَأَكْرَهُ لَهُمْ مَا أَكْرَهُ لَهَا.",
        "اللَّهُمَّ لَا تَجْعَلْ فِي قَلْبِي غِلًّا لِلَّذِينَ آمَنُوا، وَارْزُقْنِي صَفَاءَ النَّفْسِ.",
        "اللَّهُمَّ احْفَظْنِي مِنَ الْكِبْرِ وَالْعُجْبِ، وَارْزُقْنِي تَوَاضُعًا وَإِخْلَاصًا.",
        "اللَّهُمَّ اجْعَلْنِي مُبَادِرًا إِلَى الْخَيْرِ، سَرِيعًا إِلَى التَّوْبَةِ، بَعِيدًا عَنِ الْغَفْلَةِ.",
        "اللَّهُمَّ إِنِّي أَسْأَلُكَ فَرَحًا لَا يَزُولُ، وَرَاحَةً لَا تَنْقَطِعُ، وَقُرْبًا مِنْكَ دَائِمًا."
    ]
}

def normalize_live_bio_religion(religion):
    value = str(religion or "").strip().lower()
    aliases = {
        "مسلم": "islam", "الإسلام": "islam", "اسلام": "islam",
        "مسيحي": "christian", "المسيحية": "christian",
    }
    value = aliases.get(value, value)
    return value if value in LIVE_BIO_NAMES else ""

def bio_verses_for(religion):
    religion = normalize_live_bio_religion(religion)
    return [str(item).strip() for item in LIVE_BIO_DEFAULTS.get(religion, [])
            if str(item).strip() and len(str(item).strip()) <= 140]


LIVE_BIO_INTERVAL_CHOICES = {
    15: "15 دقيقة", 30: "30 دقيقة", 60: "ساعة", 180: "3 ساعات",
    360: "6 ساعات", 720: "12 ساعة", 1440: "24 ساعة",
}


async def get_live_bio_data(owner_id):
    await ensure_account_settings(owner_id)
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT live_bio_enabled, live_bio_religion, live_bio_verses, live_bio_custom_verses, "
        "live_bio_custom_texts, live_bio_mode, live_bio_interval_minutes, "
        "live_bio_custom_interval_minutes, live_bio_religious_interval_minutes, "
        "live_bio_last_updated, live_bio_index "
        "FROM settings WHERE owner_id=?",
        (owner_id,),
    )
    await conn.close()
    if not row:
        return {"enabled": False, "religion": "", "verses": [], "religious_verses": [],
                "custom_verses": [], "custom_by_religion": {}, "custom_texts": [],
                "mode": "custom", "interval_minutes": 360,
                "custom_interval_minutes": 360, "religious_interval_minutes": 360,
                "last_updated": 0, "index": 0}

    religion = normalize_live_bio_religion(row["live_bio_religion"])
    try:
        custom_by_religion = json.loads(row["live_bio_custom_verses"] or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        custom_by_religion = {}
    if not isinstance(custom_by_religion, dict):
        custom_by_religion = {}
    custom_by_religion = {
        key: [str(v).strip() for v in custom_by_religion.get(key, [])
              if str(v).strip() and len(str(v).strip()) <= 140]
        for key in LIVE_BIO_NAMES
        if isinstance(custom_by_religion.get(key, []), list)
    }
    custom_verses = list(custom_by_religion.get(religion, []))
    religious_verses = bio_verses_for(religion)
    try:
        custom_texts = json.loads(row["live_bio_custom_texts"] or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        custom_texts = []
    if not isinstance(custom_texts, list):
        custom_texts = []
    custom_texts = [str(v).strip() for v in custom_texts if str(v).strip() and len(str(v).strip()) <= 140]
    mode = row["live_bio_mode"] if row["live_bio_mode"] in ("custom", "religious") else "custom"
    try:
        interval_minutes = int(row["live_bio_interval_minutes"] or 360)
    except (TypeError, ValueError):
        interval_minutes = 360
    try:
        custom_interval_minutes = int(row["live_bio_custom_interval_minutes"] or interval_minutes)
    except (TypeError, ValueError):
        custom_interval_minutes = interval_minutes
    try:
        religious_interval_minutes = int(row["live_bio_religious_interval_minutes"] or interval_minutes)
    except (TypeError, ValueError):
        religious_interval_minutes = interval_minutes
    return {
        "enabled": bool(row["live_bio_enabled"]), "religion": religion,
        "verses": religious_verses, "religious_verses": religious_verses,
        "custom_verses": custom_verses, "custom_by_religion": custom_by_religion,
        "custom_texts": custom_texts, "mode": mode,
        "interval_minutes": religious_interval_minutes if mode == "religious" else custom_interval_minutes,
        "custom_interval_minutes": custom_interval_minutes,
        "religious_interval_minutes": religious_interval_minutes,
        "last_updated": int(row["live_bio_last_updated"] or 0),
        "index": int(row["live_bio_index"] or 0),
    }

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
async def set_live_bio_data(owner_id, *, enabled=None, religion=None, custom_by_religion=None,
                            custom_texts=None, mode=None, interval_minutes=None, interval_mode=None,
                            last_updated=None, index=None):
    await ensure_account_settings(owner_id)
    conn = await db()
    values = []
    assignments = []
    if enabled is not None:
        assignments.append("live_bio_enabled=?"); values.append(int(bool(enabled)))
    if religion is not None:
        assignments.append("live_bio_religion=?"); values.append(religion)
    if custom_by_religion is not None:
        assignments.append("live_bio_custom_verses=?")
        values.append(json.dumps(custom_by_religion, ensure_ascii=False))
    if custom_texts is not None:
        assignments.append("live_bio_custom_texts=?")
        values.append(json.dumps(custom_texts, ensure_ascii=False))
    if mode is not None:
        assignments.extend(["live_bio_mode=?", "live_bio_mode_migrated=1"])
        values.append(mode)
    if interval_minutes is not None:
        interval_column = "live_bio_religious_interval_minutes" if interval_mode == "religious" else "live_bio_custom_interval_minutes"
        assignments.append(f"{interval_column}=?"); values.append(int(interval_minutes))
        assignments.append("live_bio_interval_minutes=?"); values.append(int(interval_minutes))
    if last_updated is not None:
        assignments.append("live_bio_last_updated=?"); values.append(int(last_updated))
    if index is not None:
        assignments.append("live_bio_index=?"); values.append(int(index))
    if assignments:
        values.append(owner_id)
        await conn.execute(f"UPDATE settings SET {', '.join(assignments)} WHERE owner_id=?", values)
        await conn.commit()
    await conn.close()

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def live_bio_keyboard(data):
    enabled = data["enabled"]
    mode = data["mode"]
    if enabled and mode == "custom":
        toggle_label, toggle_style = "تعطيل البايو", "danger"
    elif enabled:
        toggle_label, toggle_style = "استخدام البايو العادي", "primary"
    elif mode == "custom":
        toggle_label, toggle_style = "تفعيل البايو", "success"
    else:
        toggle_label, toggle_style = "تفعيل البايو العادي", "success"
    rows = [
        [InlineKeyboardButton(text=toggle_label, callback_data="live_bio_toggle", style=toggle_style, icon_custom_emoji_id="6206110936789423908" if enabled else "6206479140040743133")],
        [InlineKeyboardButton(text="إضافة بايو", callback_data="live_bio_add", style="primary", icon_custom_emoji_id="5886473311637999700"), InlineKeyboardButton(text="حذف بايو", callback_data="live_bio_delete", style="danger", icon_custom_emoji_id="5879896690210639947")],
        [InlineKeyboardButton(text="عرض الكل", callback_data="live_bio_list", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text=f"ضبط مدة التغيير ({LIVE_BIO_INTERVAL_CHOICES.get(data['custom_interval_minutes'], str(data['custom_interval_minutes']) + ' دقيقة')})", callback_data="live_bio_duration_custom", style="primary", icon_custom_emoji_id="5850317551090800862")],
        [InlineKeyboardButton(text="بايو ديني", callback_data="live_bio_religious", style="primary", icon_custom_emoji_id="5769248574499983619")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def religious_bio_keyboard(data):
    religion = data["religion"]
    if religion not in LIVE_BIO_NAMES:
        return religious_bio_choice_keyboard("live_bio")
    enabled_here = data["enabled"] and data["mode"] == "religious"
    if enabled_here:
        toggle_label, toggle_style = "تعطيل البايو الديني", "danger"
    elif data["enabled"]:
        toggle_label, toggle_style = "استخدام البايو الديني", "primary"
    else:
        toggle_label, toggle_style = "تفعيل البايو الديني", "success"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_label, callback_data="live_bio_religious_toggle", style=toggle_style, icon_custom_emoji_id="5769248574499983619")],
        [InlineKeyboardButton(text="تغيير الديانة", callback_data="live_bio_change", style="primary", icon_custom_emoji_id="5233557335397389550")],
        [InlineKeyboardButton(text=f"ضبط مدة التغيير ({LIVE_BIO_INTERVAL_CHOICES.get(data['religious_interval_minutes'], str(data['religious_interval_minutes']) + ' دقيقة')})", callback_data="live_bio_duration_religious", style="primary", icon_custom_emoji_id="5850317551090800862")],
        [InlineKeyboardButton(text="رجوع", callback_data="live_bio", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def religious_bio_choice_keyboard(back_callback):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="مسلم", callback_data="live_bio_religion_islam", style="primary", icon_custom_emoji_id=LIVE_BIO_EMOJIS["islam"]),
         InlineKeyboardButton(text="مسيحي", callback_data="live_bio_religion_christian", style="primary", icon_custom_emoji_id=LIVE_BIO_EMOJIS["christian"])],
        [InlineKeyboardButton(text="رجوع", callback_data=back_callback, style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])


async def render_live_bio(call, owner_id=None):
    owner_id = owner_id or await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner_id)
    mode_name = "البايو العادي" if data["mode"] == "custom" else f"البايو الديني — {LIVE_BIO_NAMES.get(data['religion'], 'لم تُحدد الديانة')}"
    text = (
        "<tg-emoji emoji-id='5769248574499983619'>✍️</tg-emoji> <b>البايو الحي</b>\n\n"
        f"الحالة: <b>{'مفعّل' if data['enabled'] else 'معطّل'}</b>\n"
        f"النوع الحالي: <b>{html.escape(mode_name)}</b>\n"
        f"البايوهات العادية المحفوظة: <b>{len(data['custom_texts'])}</b>\n"
        f"مدة تغيير البايو العادي: <b>{LIVE_BIO_INTERVAL_CHOICES.get(data['custom_interval_minutes'], str(data['custom_interval_minutes']) + ' دقيقة')}</b>"
    )
    await call.message.edit_text(text, reply_markup=live_bio_keyboard(data), parse_mode="HTML")


async def render_religious_bio(call, owner_id=None):
    owner_id = owner_id or await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner_id)
    if data["religion"] in LIVE_BIO_NAMES:
        text = (
            f"<b>البايو الديني — {LIVE_BIO_NAMES[data['religion']]}</b>\n\n"
            f"الحالة: <b>{'مفعّل' if data['enabled'] and data['mode'] == 'religious' else 'غير مفعّل'}</b>\n"
            f"النصوص الجاهزة: <b>{len(data['religious_verses'])}</b>\n"
            f"مدة التغيير: <b>{LIVE_BIO_INTERVAL_CHOICES.get(data['religious_interval_minutes'], str(data['religious_interval_minutes']) + ' دقيقة')}</b>\n\n"
            "البايو الديني جاهز؛ تقدر تفعّله أو تغيّر الديانة."
        )
    else:
        text = "<b>البايو الديني</b>\n\nاختار: مسلم أم مسيحي؟"
    await call.message.edit_text(text, reply_markup=religious_bio_keyboard(data), parse_mode="HTML")


async def live_bio_content(data, mode=None):
    mode = mode or data["mode"]
    if mode == "religious":
        if data["religion"] not in LIVE_BIO_NAMES:
            return []
        return data["religious_verses"]
    return data["custom_texts"]


async def get_editable_bio_connection(bot, owner_id):
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT connection_id FROM business WHERE user_id=? AND enabled=1 ORDER BY can_edit_bio DESC",
        (owner_id,),
    )
    await conn.close()
    for row in rows:
        try:
            current = await refresh_business_connection(bot, row["connection_id"])
            rights = current.rights
            if current.is_enabled and rights and getattr(rights, "can_edit_bio", False):
                return row["connection_id"]
        except Exception:
            logger.exception("Could not refresh business bio rights for owner %s", owner_id)
    return None
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

def telegram_bio_limit(text):
    text = unicodedata.normalize("NFKC", str(text or "").strip())
    text = " ".join(ch for ch in text.split())
    result = []
    units = 0
    for ch in text:
        size = len(ch.encode("utf-16-le")) // 2
        if units + size > 140:
            break
        result.append(ch)
        units += size
    return "".join(result)

async def set_business_bio(bot, connection_id, bio):
    bio_text = telegram_bio_limit(bio)
    try:
        result = await bot.set_business_account_bio(
            business_connection_id=connection_id, bio=bio_text
        )
        return bool(result)
    except Exception:
        plain_text = telegram_bio_limit("".join(
            ch for ch in bio_text if unicodedata.category(ch) != "Mn"
        ))
        if plain_text and plain_text != bio_text:
            try:
                result = await bot.set_business_account_bio(
                    business_connection_id=connection_id, bio=plain_text
                )
                return bool(result)
            except Exception:
                logger.exception("Failed to update business account bio after Arabic fallback")
        else:
            logger.exception("Failed to update business account bio")
        return False


async def apply_live_bio(bot, owner_id, advance=False, connection_id=None):
    data = await get_live_bio_data(owner_id)
    items = await live_bio_content(data)
    if not data["enabled"] or not items:
        return False
    if connection_id is None:
        connection_id = await get_editable_bio_connection(bot, owner_id)
    if not connection_id:
        return False
    index = data["index"] % len(items)
    if await set_business_bio(bot, connection_id, items[index]):
        now = int(datetime.now(timezone.utc).timestamp())
        await set_live_bio_data(owner_id,
                                index=(index + 1) % len(items) if advance else index,
                                last_updated=now)
        return True
    return False


async def _toggle_live_bio(call, target_mode):
    owner = await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner)
    if data["enabled"] and data["mode"] == target_mode:
        await set_live_bio_data(owner, enabled=False)
        connection_id = await get_editable_bio_connection(call.bot, owner)
        cleared = bool(connection_id and await set_business_bio(call.bot, connection_id, ""))
        if target_mode == "religious":
            await render_religious_bio(call, owner)
        else:
            await render_live_bio(call, owner)
        if cleared:
            await call.answer("تم تعطيل البايو ومسح النص الحالي.")
        else:
            await call.answer("تم إيقاف التغيير، لكن تعذر مسح البايو. تأكد من صلاحية can_edit_bio.", show_alert=True)
        return

    items = await live_bio_content(data, target_mode)
    if target_mode == "religious" and data["religion"] not in LIVE_BIO_NAMES:
        await render_religious_bio(call, owner)
        await call.answer("اختار مسلم أو مسيحي أولاً.", show_alert=True)
        return
    if not items:
        await call.answer("أضف بايو واحدًا على الأقل أولاً.", show_alert=True)
        return
    connection_id = await get_editable_bio_connection(call.bot, owner)
    if not connection_id:
        await call.answer("لا يوجد اتصال Business بصلاحية تعديل البايو. فعّل can_edit_bio.", show_alert=True)
        return
    await set_live_bio_data(owner, mode=target_mode, enabled=True, index=0, last_updated=0)
    applied = await apply_live_bio(call.bot, owner, advance=True, connection_id=connection_id)
    if not applied:
        await set_live_bio_data(owner, mode=data["mode"], enabled=data["enabled"], index=data["index"], last_updated=data["last_updated"])
        await call.answer("تعذر تحديث البايو؛ لم يتم تغيير الوضع.", show_alert=True)
        return
    if target_mode == "religious":
        await render_religious_bio(call, owner)
    else:
        await render_live_bio(call, owner)
    await call.answer("تم تفعيل البايو وتحديثه فورًا.")


@router.callback_query(F.data == "live_bio")
async def live_bio(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    await render_live_bio(call)
    await call.answer()


@router.callback_query(F.data == "live_bio_toggle")
async def live_bio_toggle(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    await _toggle_live_bio(call, "custom")


@router.callback_query(F.data == "live_bio_religious")
async def live_bio_religious(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    await render_religious_bio(call)
    await call.answer()


@router.callback_query(F.data == "live_bio_change")
async def live_bio_change(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "اختار الديانة الجديدة للبايو الديني:",
        reply_markup=religious_bio_choice_keyboard("live_bio_religious"),
    )
    await call.answer()

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

@router.callback_query(F.data == "live_bio_religious_toggle")
async def live_bio_religious_toggle(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    await _toggle_live_bio(call, "religious")


@router.callback_query(F.data.startswith("live_bio_religion_"))
async def live_bio_choose_religion(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    religion = call.data.removeprefix("live_bio_religion_")
    if religion not in LIVE_BIO_NAMES:
        await call.answer("اختيار غير صالح.", show_alert=True); return
    owner = await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner)
    await set_live_bio_data(owner, religion=religion, mode="religious", index=0, last_updated=0)
    updated = True
    if data["enabled"]:
        updated = await apply_live_bio(call.bot, owner, advance=True)
        if not updated:
            await set_live_bio_data(
                owner,
                religion=data["religion"],
                mode=data["mode"],
                index=data["index"],
                last_updated=data["last_updated"],
            )
    await render_religious_bio(call, owner)
    if data["enabled"] and not updated:
        await call.answer("لم أستطع تحديث البايو الآن؛ تحقق من اتصال Business وصلاحية تعديل البايو.", show_alert=True)
    elif data["enabled"]:
        await call.answer(f"تم اختيار {LIVE_BIO_NAMES[religion]} وتحديث البايو فورًا.")
    else:
        await call.answer(f"تم اختيار {LIVE_BIO_NAMES[religion]}.")


@router.callback_query(F.data == "live_bio_add")
async def live_bio_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.update_data(bio_kind="custom")
    await state.set_state(LiveBioSG.add_verse)
    await call.message.edit_text("أرسل نص البايو العادي (بحد أقصى 140 حرفًا).", reply_markup=cancel_kb())
    await call.answer()


@router.callback_query(F.data == "live_bio_religious_add")
async def live_bio_religious_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة؛ من هنا التفعيل أو تغيير الديانة فقط.", show_alert=True)


@router.message(LiveBioSG.add_verse)
async def live_bio_add_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    value = (message.text or "").strip()
    if not value or len(value) > 140:
        await message.answer("أرسل نصًا صحيحًا لا يتجاوز 140 حرفًا.")
        return
    state_data = await state.get_data()
    kind = state_data.get("bio_kind", "custom")
    if kind == "religious":
        await state.clear()
        await message.answer("النصوص الدينية جاهزة في قسم البايو الديني ولا تُضاف يدويًا.", reply_markup=back_kb("live_bio_religious"))
        return
    owner = await settings_owner(message.from_user.id)
    data = await get_live_bio_data(owner)
    if value in data["custom_texts"]:
        await state.clear(); await message.answer("البايو موجود بالفعل.", reply_markup=back_kb("live_bio")); return
    custom_texts = list(data["custom_texts"]) + [value]
    new_index = len(custom_texts) - 1
    await set_live_bio_data(owner, custom_texts=custom_texts, mode="custom", index=new_index, last_updated=0)
    return_to = "live_bio"
    active_in_kind = data["enabled"]
    await state.clear()
    applied = True
    if active_in_kind:
        applied = await apply_live_bio(message.bot, owner, advance=False)
    confirmation = "تمت إضافة النص للحساب."
    if active_in_kind:
        confirmation += "\n" + ("وتم تطبيقه فورًا." if applied else "تعذر تطبيقه الآن؛ راجع صلاحية تعديل البايو.")
    await message.answer(confirmation, reply_markup=back_kb(return_to))
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

async def render_bio_text_list(call, owner_id, kind="custom", page=0):
    data = await get_live_bio_data(owner_id)
    items = data["custom_texts"] if kind == "custom" else data["religious_verses"]
    return_to = "live_bio" if kind == "custom" else "live_bio_religious"
    title = "البايوهات المحفوظة" if kind == "custom" else ("آيات الكتاب المقدس" if data["religion"] == "christian" else "الأدعية الإسلامية")
    if not items:
        await call.message.edit_text("لا توجد نصوص محفوظة.", reply_markup=back_kb(return_to))
        return
    per_page = 5
    pages = (len(items) + per_page - 1) // per_page
    page = max(0, min(int(page), pages - 1))
    text = f"<b>{title}</b> — {page + 1}/{pages}\n\n" + "\n\n".join(html.escape(item, quote=False) for item in items[page*per_page:(page+1)*per_page])
    prefix = "live_bio_regular_list_page_" if kind == "custom" else "live_bio_religious_list_page_"
    rows = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="السابق", callback_data=f"{prefix}{page-1}", style="primary"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(text="التالي", callback_data=f"{prefix}{page+1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="رجوع", callback_data=return_to, style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")


async def render_bio_delete_list(call, owner_id, kind="custom", page=0):
    data = await get_live_bio_data(owner_id)
    items = data["custom_texts"] if kind == "custom" else data["custom_verses"]
    return_to = "live_bio" if kind == "custom" else "live_bio_religious"
    if not items:
        message = "لا توجد بايوهات أضفتها لحذفها." if kind == "custom" else "لا توجد إضافات دينية لهذا الحساب لحذفها. النصوص الافتراضية تبقى متاحة."
        await call.message.edit_text(message, reply_markup=back_kb(return_to))
        return
    per_page = 8
    pages = (len(items) + per_page - 1) // per_page
    page = max(0, min(int(page), pages - 1))
    start = page * per_page
    del_prefix = "live_bio_regular_del_" if kind == "custom" else "live_bio_religious_del_"
    page_prefix = "live_bio_regular_delete_page_" if kind == "custom" else "live_bio_religious_delete_page_"
    rows = [[InlineKeyboardButton(text=item[:45], callback_data=f"{del_prefix}{start+i}", style="danger", icon_custom_emoji_id="5879896690210639947")] for i, item in enumerate(items[start:start+per_page])]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="السابق", callback_data=f"{page_prefix}{page-1}", style="primary"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(text="التالي", callback_data=f"{page_prefix}{page+1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="رجوع", callback_data=return_to, style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(f"اختر النص الذي تريد حذفه ({page+1}/{pages}):", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "live_bio_list")
async def live_bio_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_bio_text_list(call, await settings_owner(call.from_user.id), "custom", 0)
    await call.answer()


@router.callback_query(F.data.startswith("live_bio_regular_list_page_"))
async def live_bio_regular_list_page(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_bio_text_list(call, await settings_owner(call.from_user.id), "custom", int(call.data.rsplit("_", 1)[-1]))
    await call.answer()


@router.callback_query(F.data == "live_bio_religious_list")
async def live_bio_religious_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة؛ لا تحتاج لإدارة قائمة يدوية.", show_alert=True)


@router.callback_query(F.data.startswith("live_bio_religious_list_page_"))
async def live_bio_religious_list_page(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة؛ لا تحتاج لإدارة قائمة يدوية.", show_alert=True)


@router.callback_query(F.data == "live_bio_delete")
async def live_bio_delete(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_bio_delete_list(call, await settings_owner(call.from_user.id), "custom", 0)
    await call.answer()


@router.callback_query(F.data.startswith("live_bio_regular_delete_page_"))
async def live_bio_regular_delete_page(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_bio_delete_list(call, await settings_owner(call.from_user.id), "custom", int(call.data.rsplit("_", 1)[-1]))
    await call.answer()


@router.callback_query(F.data == "live_bio_religious_delete")
async def live_bio_religious_delete(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة؛ لا توجد إضافات يدوية لحذفها.", show_alert=True)


@router.callback_query(F.data.startswith("live_bio_religious_delete_page_"))
async def live_bio_religious_delete_page(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة؛ لا توجد إضافات يدوية لحذفها.", show_alert=True)


async def delete_bio_entry(call, kind, index):
    owner = await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner)
    notice = "تم حذف النص."
    show_alert = False
    if kind == "custom":
        items = list(data["custom_texts"])
        return_to = "live_bio"
        if not 0 <= index < len(items):
            await call.answer("البايو غير موجود.", show_alert=True); return
        items.pop(index)
        await set_live_bio_data(owner, custom_texts=items)
        if data["enabled"] and data["mode"] == "custom":
            if items:
                await set_live_bio_data(owner, index=data["index"] % len(items), last_updated=0)
                if not await apply_live_bio(call.bot, owner, advance=False):
                    notice = "حُذف النص، لكن تعذّر تحديث البايو الحالي. راجع صلاحية can_edit_bio."
                    show_alert = True
            else:
                await set_live_bio_data(owner, enabled=False)
                connection_id = await get_editable_bio_connection(call.bot, owner)
                cleared = bool(connection_id and await set_business_bio(call.bot, connection_id, ""))
                if not cleared:
                    notice = "حُذف آخر بايو وأُوقف التغيير، لكن تعذّر مسح البايو الحالي. راجع صلاحية can_edit_bio."
                    show_alert = True
    else:
        items = list(data["custom_verses"])
        return_to = "live_bio_religious"
        if not 0 <= index < len(items):
            await call.answer("الإضافة غير موجودة.", show_alert=True); return
        items.pop(index)
        custom_map = dict(data["custom_by_religion"])
        custom_map[data["religion"]] = items
        await set_live_bio_data(owner, custom_by_religion=custom_map)
        updated = await get_live_bio_data(owner)
        await set_live_bio_data(owner, index=updated["index"] % len(updated["religious_verses"]) if updated["religious_verses"] else 0, last_updated=0)
        if data["enabled"] and data["mode"] == "religious":
            if not await apply_live_bio(call.bot, owner, advance=False):
                notice = "حُذفت الإضافة، لكن تعذّر تحديث البايو الحالي. راجع صلاحية can_edit_bio."
                show_alert = True
    if kind == "religious":
        await render_religious_bio(call, owner)
    else:
        await render_live_bio(call, owner)
    await call.answer(notice, show_alert=show_alert)


@router.callback_query(F.data.startswith("live_bio_regular_del_"))
async def live_bio_regular_del(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await delete_bio_entry(call, "custom", int(call.data.rsplit("_", 1)[-1]))


@router.callback_query(F.data.startswith("live_bio_religious_del_"))
async def live_bio_religious_del(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await render_religious_bio(call)
    await call.answer("النصوص الدينية جاهزة ولا تُحذف من هذا القسم.", show_alert=True)


@router.callback_query(F.data == "live_bio_duration")
async def live_bio_duration(call: CallbackQuery):
    await show_live_bio_duration(call, "custom")
@router.callback_query(F.data == "live_bio_duration_custom")
async def live_bio_custom_duration(call: CallbackQuery):
    await show_live_bio_duration(call, "custom")
@router.callback_query(F.data == "live_bio_duration_religious")
async def live_bio_religious_duration(call: CallbackQuery):
    await show_live_bio_duration(call, "religious")
async def show_live_bio_duration(call: CallbackQuery, mode):
    if not await is_admin(call.from_user.id): return
    data = await get_live_bio_data(await settings_owner(call.from_user.id))
    interval_key = "religious_interval_minutes" if mode == "religious" else "custom_interval_minutes"
    back_callback = "live_bio_religious" if mode == "religious" else "live_bio"
    bio_label = "الديني" if mode == "religious" else "العادي"
    rows = [[InlineKeyboardButton(text=label, callback_data=f"live_bio_duration_set_{mode}_{minutes}", style="success" if minutes == data[interval_key] else "primary")] for minutes, label in LIVE_BIO_INTERVAL_CHOICES.items()]
    rows.append([InlineKeyboardButton(text="رجوع", callback_data=back_callback, style="danger", icon_custom_emoji_id="5445365692004071819")])
    await call.message.edit_text(f"اختار المدة بين كل تغيير للبايو {bio_label}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()
@router.callback_query(F.data.startswith("live_bio_duration_"))
async def live_bio_set_duration(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    try:
        parts = call.data.split("_")
        if len(parts) == 6 and parts[3] == "set":
            interval_mode = parts[4]
            minutes = int(parts[5])
        else:
            interval_mode = "custom"
            minutes = int(parts[-1])
    except ValueError:
        await call.answer("المدة غير صالحة.", show_alert=True); return
    if interval_mode not in ("custom", "religious") or minutes not in LIVE_BIO_INTERVAL_CHOICES:
        await call.answer("اختار مدة من القائمة.", show_alert=True); return
    owner = await settings_owner(call.from_user.id)
    data = await get_live_bio_data(owner)
    update_fields = {"interval_minutes": minutes, "interval_mode": interval_mode}
    if data["mode"] == interval_mode:
        update_fields["last_updated"] = int(datetime.now(timezone.utc).timestamp())
    await set_live_bio_data(owner, **update_fields)
    if interval_mode == "religious":
        await render_religious_bio(call, owner)
    else:
        await render_live_bio(call, owner)
    await call.answer(f"تم ضبط المدة: {LIVE_BIO_INTERVAL_CHOICES[minutes]}.")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

async def live_bio_worker(bot):
    while True:
        await asyncio.sleep(LIVE_BIO_CHECK_INTERVAL.total_seconds())
        try:
            conn = await db()
            rows = await conn.execute_fetchall(
                "SELECT owner_id, live_bio_mode, live_bio_interval_minutes, "
                "live_bio_custom_interval_minutes, live_bio_religious_interval_minutes, "
                "live_bio_last_updated FROM settings WHERE live_bio_enabled=1"
            )
            await conn.close()
            now = int(datetime.now(timezone.utc).timestamp())
            for row in rows:
                interval_value = (
                    row["live_bio_religious_interval_minutes"]
                    if row["live_bio_mode"] == "religious"
                    else row["live_bio_custom_interval_minutes"]
                )
                interval = max(1, int(interval_value or row["live_bio_interval_minutes"] or 360)) * 60
                last_updated = int(row["live_bio_last_updated"] or 0)
                if now - last_updated < interval:
                    continue
                try:
                    await apply_live_bio(bot, row["owner_id"], advance=True)
                except Exception:
                    logger.exception("Live bio update failed for owner %s", row["owner_id"])
        except Exception:
            logger.exception("Live bio worker cycle failed")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
CLOCK_OFFSET_MINUTES = 0
CLOCK_DIGITS = ["𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿", "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"]

def format_clock_time(hour24, minute, style):
    hour12 = hour24 % 12 or 12 
    raw = f"{hour12}:{minute:02d}"
    digits = CLOCK_DIGITS[int(style) % len(CLOCK_DIGITS)]
    trans = str.maketrans("0123456789", digits)
    return raw.translate(trans)

def clock_text(style):
    now = datetime.now(timezone(timedelta(hours=3))) + timedelta(minutes=CLOCK_OFFSET_MINUTES)
    return format_clock_time(now.hour, now.minute, style)

def clean_clock_suffix(name):
    if not name:
        return ""
    digit_sets = CLOCK_DIGITS + ["𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡𝟘"]
    digit_chars = "".join(digit_sets) + "0123456789"
    digit_class = re.escape(digit_chars)
    period = r"(?:\s*(?:[صم]|AM|PM))?"
    cleaned = re.sub(rf"\s+[{digit_class}]{{1,2}}:[{digit_class}]{{2}}{period}$", "", str(name), flags=re.IGNORECASE)
    cleaned = re.sub(rf"\s+[{digit_class}]{{1,2}}$", "", cleaned)
    return cleaned.strip()

def live_clock_kb(enabled, style=0):
    rows = [[InlineKeyboardButton(text=f"{'تعطيل' if enabled else 'تفعيل'} الساعة الحية", callback_data="live_clock_toggle", style="danger" if enabled else "success", icon_custom_emoji_id="6206479140040743133" if enabled else "6206110936789423908")]]
    for i in range(0, len(CLOCK_DIGITS), 2):
        rows.append([InlineKeyboardButton(text=f"{clock_text(i)}", callback_data=f"clock_style_{i}", style="primary" if i != style else "success", icon_custom_emoji_id="6206479140040743133" if i == style else "5904219717073114606"), InlineKeyboardButton(text=f"{clock_text(i+1)}", callback_data=f"clock_style_{i+1}", style="primary" if i+1 != style else "success", icon_custom_emoji_id="6206479140040743133" if i+1 == style else "5904219717073114606")])
    rows.append([InlineKeyboardButton(text="رجوع", callback_data="advanced", style="danger", icon_custom_emoji_id="5445365692004071819")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def set_business_name(bot, connection_id, first_name, last_name):
    try:
        await bot.set_business_account_name(
            business_connection_id=connection_id,
            first_name=first_name,
            last_name=last_name,
        )
        return True
    except Exception:
        logger.exception("Failed to update business account name")
        return False
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
async def refresh_business_connection(bot, connection_id):
    current = await bot.get_business_connection(business_connection_id=connection_id)
    enabled = int(bool(current.is_enabled))
    can_edit_name = int(bool(current.rights and current.rights.can_edit_name))
    conn = await db()
    await conn.execute(
        "UPDATE business SET enabled=?, can_edit_name=?, can_edit_bio=? WHERE connection_id=?",
        (enabled, can_edit_name, int(bool(getattr(current.rights, "can_edit_bio", False))), connection_id),
    )
    await conn.commit()
    await conn.close()
    return current

@router.callback_query(F.data == "live_clock")
async def live_clock(call: CallbackQuery):
    owner = call.from_user.id
    conn = await db(); row = await fetchone(conn, "SELECT clock_enabled, clock_style FROM business WHERE user_id=? AND enabled=1 LIMIT 1", (owner,)); await conn.close()
    enabled = bool(row and row["clock_enabled"]); style = int(row["clock_style"] if row else 0)
    await call.message.edit_text(section_message("الساعة الحية", "⏰", "يضع البوت الساعة الحالية في خانة الاسم الأخير لحسابك ويحدّثها تلقائياً كل دقيقة.", "اكتب اسمك في خانة الاسم الأول، وعند التعطيل يعود الاسم الأخير الأصلي."), reply_markup=live_clock_kb(enabled, style), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("clock_style_"))
async def clock_style(call: CallbackQuery):
    owner = call.from_user.id
    try:
        style = int(call.data.rsplit("_", 1)[-1])
    except (TypeError, ValueError):
        await call.answer("اختيار شكل الساعة غير صالح.", show_alert=True)
        return
    if not 0 <= style < len(CLOCK_DIGITS):
        await call.answer("اختيار شكل الساعة غير صالح.", show_alert=True)
        return

    conn = await db()
    await conn.execute(
        "UPDATE business SET clock_style=? WHERE user_id=? AND enabled=1",
        (style, owner),
    )
    await conn.commit()
    row = await fetchone(
        conn,
        "SELECT connection_id, clock_enabled FROM business WHERE user_id=? AND enabled=1 LIMIT 1",
        (owner,),
    )
    await conn.close()
    if row and row["clock_enabled"]:
        try:
            current = await refresh_business_connection(call.bot, row["connection_id"])
            if current.is_enabled and current.rights and current.rights.can_edit_name:
                await set_business_name(
                    call.bot,
                    row["connection_id"],
                    clean_clock_suffix(current.user.first_name or "") or " ",
                    clock_text(style),
                )
        except Exception:
            logger.exception("Failed to refresh business name while changing clock style")

    await call.message.edit_reply_markup(
        reply_markup=live_clock_kb(bool(row and row["clock_enabled"]), style)
    )
    await call.answer("تم اختيار شكل الساعة")
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

@router.callback_query(F.data == "live_clock_toggle")
async def live_clock_toggle(call: CallbackQuery):
    owner = call.from_user.id
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT connection_id, original_name, original_last_name, clock_enabled, clock_style, can_edit_name, enabled "
        "FROM business WHERE user_id=? ORDER BY enabled DESC LIMIT 1",
        (owner,),
    )
    await conn.close()
    if not row:
        await call.answer(
            "لا يوجد اتصال محفوظ لهذا الحساب. أعد ربط البوت بحساب Telegram Business.",
            show_alert=True,
        )
        return

    try:
        current = await refresh_business_connection(call.bot, row["connection_id"])
    except Exception:
        logger.exception("Failed to refresh Telegram Business connection before enabling live clock")
        await call.answer(
            "تعذر التحقق من اتصال Telegram الآن؛ لم أرفض الصلاحية. حاول مرة أخرى بعد قليل.",
            show_alert=True,
        )
        return

    if not current.is_enabled:
        await call.answer(
            "اتصال Telegram Business غير مفعّل حاليًا. أعد تفعيله ثم حاول مجددًا.",
            show_alert=True,
        )
        return
    if not (current.rights and current.rights.can_edit_name):
        await call.answer(
            "تيليجرام لا يرسل للبوت صلاحية تعديل اسم الحساب. راجع صلاحية تعديل الاسم في إعدادات Telegram Business.",
            show_alert=True,
        )
        return
    new_enabled = 0 if row["clock_enabled"] else 1
    # اترك الاسم الأول كما هو؛ نظّف فقط ساعة قديمة من الإصدارات السابقة.
    if new_enabled:
        first_name = clean_clock_suffix(current.user.first_name or row["original_name"] or "") or " "
        original_last_name = current.user.last_name or ""
        last_name = clock_text(row["clock_style"])
    else:
        first_name = clean_clock_suffix(row["original_name"] or current.user.first_name or "") or " "
        original_last_name = row["original_last_name"]
    
        if original_last_name is None:
            original_last_name = current.user.last_name or ""
        last_name = original_last_name
    conn = await db()
    if new_enabled:
        await conn.execute(
            "UPDATE business SET clock_enabled=1, original_name=?, original_last_name=? WHERE connection_id=?",
            (first_name, original_last_name, row["connection_id"]),
        )
    else:
        await conn.execute(
            "UPDATE business SET clock_enabled=0 WHERE connection_id=?",
            (row["connection_id"],),
        )
    await conn.commit()
    await conn.close()
    if await set_business_name(call.bot, row["connection_id"], first_name, last_name):
        await call.answer("تم تفعيل الساعة" if new_enabled else "تم تعطيل الساعة")
    else:
        conn = await db()
        await conn.execute("UPDATE business SET clock_enabled=? WHERE connection_id=?", (int(not new_enabled), row["connection_id"]))
        await conn.commit()
        await conn.close()
        await call.answer("تعذر تعديل اسم الحساب من Telegram.", show_alert=True)
    await live_clock(call)

async def live_clock_worker(bot):
    while True:
        conn = await db()
        rows = await conn.execute_fetchall(
            "SELECT connection_id, original_name, clock_style "
            "FROM business WHERE enabled=1 AND clock_enabled=1"
        )
        await conn.close()

        for row in rows:
            try:
                current = await bot.get_business_connection(
                    business_connection_id=row["connection_id"]
                )
                can_edit = bool(current.rights and current.rights.can_edit_name)
                if not current.is_enabled or not can_edit:
                    logger.warning("Live clock skipped for %s: connection disabled or name permission missing", row["connection_id"])
                    continue
                await set_business_name(
                    bot,
                    row["connection_id"],
                    clean_clock_suffix(current.user.first_name or "") or " ",
                    clock_text(row["clock_style"]),
                )
            except Exception:

                logger.exception("Live clock update failed for connection %s", row["connection_id"])

        now = datetime.now(timezone.utc)
        delay = 60 - now.second - (now.microsecond / 1_000_000)
        await asyncio.sleep(max(0.2, delay))

@router.business_connection()
async def business_connection(update: BusinessConnection):
    conn = await db()
    await conn.execute("""
        INSERT INTO business(connection_id, user_id, enabled, can_reply, original_name, original_last_name, can_edit_name, can_edit_bio)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(connection_id) DO UPDATE SET
        user_id=excluded.user_id,
        enabled=excluded.enabled,
        can_reply=excluded.can_reply,
        original_name=CASE WHEN business.clock_enabled=1 THEN business.original_name ELSE excluded.original_name END,
        original_last_name=CASE WHEN business.clock_enabled=1 THEN business.original_last_name ELSE excluded.original_last_name END,
        can_edit_name=excluded.can_edit_name,
        can_edit_bio=excluded.can_edit_bio
    """, (
        update.id, update.user.id, int(bool(update.is_enabled)),
        int(bool(getattr(getattr(update, "rights", None), "can_reply", False))),
        update.user.first_name or "",
        update.user.last_name or "",
        int(bool(getattr(getattr(update, "rights", None), "can_edit_name", False))),
        int(bool(getattr(getattr(update, "rights", None), "can_edit_bio", False)))
    ))
    await conn.commit()
    await conn.close()
    await ensure_account_settings(update.user.id)
    if update.is_enabled:
        await set_account_setting(update.user.id, "enabled", 1)
        await _referral_reward(update.bot, update.user.id)

    if update.is_enabled:
        txt = (
            "<tg-emoji emoji-id='5890925363067886150'>✨</tg-emoji> "
            "تم ربط حسابك بالبوت بنجاح!\nيمكنك الآن الدخول إلى لوحة التحكم."
        )
        owner_txt = f"تم ربط حساب جديد بالبوت.\nالآيدي: {update.user.id}\nاليوزر: @{update.user.username or '-'}\nالاسم: {safe_html(update.user.first_name or '')}\nمعرف الاتصال: {update.id}"
    else:
        txt = "<tg-emoji emoji-id='5341498036868634459'>⚠️</tg-emoji> تم إلغاء ربط حسابك بالبوت."
        owner_txt = f"تم إلغاء ربط حساب بالبوت.\nالمستخدم: {update.user.id}\nاليوزر: @{update.user.username or '-'}\nالاسم: {safe_html(update.user.first_name or '')}\nمعرف الاتصال: {update.id}"
    try:
        if await paid_access_allowed(update.user.id):
            await update.bot.send_message(chat_id=update.user.id, text=txt, parse_mode="HTML")
        if update.user.id != OWNER_ID:
            await update.bot.send_message(chat_id=OWNER_ID, text=owner_txt)
    except Exception:
        logger.exception("Failed to send connection notice")

@router.my_chat_member()
async def bot_chat_member_updated(update: ChatMemberUpdated, bot: Bot):
    if update.chat.type != "channel":
        return
    if not update.new_chat_member or update.new_chat_member.user.id != bot.id:
        return
    status = getattr(update.new_chat_member.status, "value", update.new_chat_member.status) or ""
    status = str(status).lower()
    title = update.chat.title or "بدون اسم"
    username = f"@{update.chat.username}" if update.chat.username else str(update.chat.id)
    conn = await db()
    old = await fetchone(conn, "SELECT chat_id FROM bot_channels WHERE chat_id=?", (update.chat.id,))
    active = status in {"administrator", "member"}
    if not active:
        await conn.execute("DELETE FROM bot_channels WHERE chat_id=?", (update.chat.id,))
        await conn.commit(); await conn.close()
        try:
            await bot.send_message(chat_id=OWNER_ID, text=(f"<blockquote><b>تم تنزيل البوت من قناة</b>\n\nالقناة: <b>{safe_html(title)}</b>\nالمعرف: <code>{safe_html(username)}</code></blockquote>"), parse_mode="HTML")
        except Exception:
            logger.exception("Failed to send channel-removed notice")
        return
    if status == "administrator":
        await conn.execute(
            "INSERT INTO bot_channels(chat_id, title, username, added_at) VALUES(?, ?, ?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title, username=excluded.username",
            (update.chat.id, title, update.chat.username or "", datetime.now(timezone.utc).isoformat())
        )
    await conn.commit(); await conn.close()
    if not old:
        try:
            role = "أدمن" if status == "administrator" else "عضو"
            await bot.send_message(chat_id=OWNER_ID, text=(f"<blockquote><b>تم رفع البوت في قناة جديدة</b>\n\nالقناة: <b>{safe_html(title)}</b>\nالمعرف: <code>{safe_html(username)}</code>\nالصلاحية: <b>{role}</b></blockquote>"), parse_mode="HTML")
        except Exception:
            logger.exception("Failed to send channel-added notice")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
async def conn2_update_subscription_prompt(connection_id, chat_id, message_id):
    conn = await db()
    await conn.execute("UPDATE customers SET last_subscription_prompt_id=? WHERE connection_id=? AND chat_id=?", (message_id, connection_id, chat_id))
    await conn.commit()
    await conn.close()


async def get_profile_details(bot, user_id, fallback_name="", fallback_username=""):
    name = fallback_name or "غير معروف"
    username = fallback_username or ""
    try:
        chat = await bot.get_chat(user_id)
        name = getattr(chat, "full_name", None) or getattr(chat, "first_name", None) or name
        username = getattr(chat, "username", None) or username
    except Exception:
        pass
    username_text = f"@{safe_html(username)}" if username else "غير متوفر"
    return safe_html(name), username_text, str(user_id)


def profile_copy_kb(name, username, user_id):
    username_value = f"@{username}" if username and username != "غير متوفر" else "غير متوفر"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="نسخ اليوزر", copy_text=CopyTextButton(text=username_value),
                style="primary", icon_custom_emoji_id="6028171274939797252"
            ),
            InlineKeyboardButton(
                text="نسخ الآيدي", copy_text=CopyTextButton(text=str(user_id)),
                style="primary", icon_custom_emoji_id="5873044297523140571"
            ),
        ],
        [InlineKeyboardButton(
            text="نسخ الاسم", copy_text=CopyTextButton(text=name),
            style="primary", icon_custom_emoji_id="5778145208411624388"
        )],
    ])


async def send_profile_card(message, target_user_id, fallback_name="", fallback_username=""):
    name, username_text, user_id_text = await get_profile_details(
        message.bot, target_user_id, fallback_name, fallback_username
    )
    caption = (
        "<b><tg-emoji emoji-id='5873044297523140571'>🆔</tg-emoji> معلومات الحساب</b>\n\n"
        f"<tg-emoji emoji-id='5778145208411624388'>👤</tg-emoji> الاسم: {name}\n"
        f"<tg-emoji emoji-id='6028171274939797252'>🔗</tg-emoji> اليوزر: {username_text}\n"
        f"<tg-emoji emoji-id='5873044297523140571'>🆔</tg-emoji> الايدي: <code>{user_id_text}</code>"
    )
    reply_markup = profile_copy_kb(name, username_text, user_id_text)
    try:
        photos = await message.bot.get_user_profile_photos(user_id=target_user_id, limit=1)
        if photos.total_count and photos.photos:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=photos.photos[0][-1].file_id,
                caption=caption,
                reply_markup=reply_markup,
                business_connection_id=message.business_connection_id,
                parse_mode="HTML",
            )
            return
    except Exception:
        logger.exception("Failed to fetch profile photo for %s", target_user_id)
    await message.bot.send_message(
        chat_id=message.chat.id,
        text=caption,
        reply_markup=reply_markup,
        business_connection_id=message.business_connection_id,
        parse_mode="HTML",
    )


def build_reply_kb(buttons, use_icons=True, use_copy_buttons=True):
    built = []
    for button in buttons:
        label = button["label"] or "زر"
        emoji_id = button["icon_custom_emoji_id"] or None
        base = {
            "text": label,
            "style": BTN_STYLE_MAP.get(button["btn_color"], "primary"),
        }
        if use_icons and button["btn_type"] != "copy":
            base["icon_custom_emoji_id"] = emoji_id or "5445128296276718145"
        try:
            if button["btn_type"] == "url":
                base["url"] = button["btn_value"]
            elif button["btn_type"] == "copy" and use_copy_buttons:
                base["copy_text"] = CopyTextButton(text=button["btn_value"])
            else:
                base["callback_data"] = f"rcopy_{button['id']}" if button["btn_type"] == "copy" else f"rtext_{button['id']}"
            built.append(InlineKeyboardButton(**base))
        except Exception:
            base.pop("icon_custom_emoji_id", None)
            base.pop("copy_text", None)
            if button["btn_type"] == "copy":
                base["callback_data"] = f"rcopy_{button['id']}"
            built.append(InlineKeyboardButton(**base))
    rows = _rows_for_reply(buttons, built)
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


@router.callback_query(F.data == "currency_tool")
async def currency_tool(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id)
    enabled = bool(await get_account_setting(owner, "currency_enabled") if await get_account_setting(owner, "currency_enabled") is not None else 1)
    await call.message.edit_text("<tg-emoji emoji-id='6050934734752582943'>💱</tg-emoji> <b>أسعار العملات الحية</b>\n\n<blockquote>اعرف قيمة أي مبلغ بعملة TON أو الدولار أو الجنيه المصري، وسيحوّلها لك تلقائيًا حسب السعر الحالي.\n\nمثال: 1ton أو 1$ أو 1جنيه.</blockquote>", reply_markup=currency_tool_kb(enabled), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "currency_toggle")
async def currency_toggle(call: CallbackQuery):
    owner = await settings_owner(call.from_user.id)
    cur = await get_account_setting(owner, "currency_enabled") or 0
    await set_account_setting(owner, "currency_enabled", 0 if cur else 1)
    await currency_tool(call)

@router.callback_query(F.data.startswith("currency_"))
async def currency_refresh_button(call: CallbackQuery):
    if call.data == "currency_show":
        await currency_show(call)
        return
    await call.answer()

@router.callback_query(F.data == "currency_show")
async def currency_show(call: CallbackQuery):
    prices = await fetch_live_prices()
    if not prices:
        await call.answer("تعذر جلب السعر الحالي، حاول بعد قليل.", show_alert=True)
        return
    values = currency_prices_text(1, "ton", prices)
    await call.message.edit_text(currency_header(1, "ton"), reply_markup=currency_keyboard(values, "ton"), parse_mode="HTML")
    await call.answer()


# ─────────────────────── ميزة الانتحال وإلغاء الانتحال ───────────────────────
_IMPERSONATE_NORM_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي", "ـ": ""
})

def _normalize_impersonate_cmd(value: str) -> str:
    if not value:
        return ""
    s = value.strip().lstrip("/!.")
    s = re.sub(r"[\u064B-\u065F\u0670]", "", s)
    s = s.translate(_IMPERSONATE_NORM_MAP).lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return " ".join(s.split())

_IMPERSONATE_START_CMDS = {
    "انتحل", "انتحال", "نتحل", "نتحال",
    "الانتحال", "انتحل حسابه", "انتحال حساب", "انتحال الحساب", "انتحل الحساب",
}

_IMPERSONATE_STOP_CMDS = {
    "الغاء الانتحال", "الغاء انتحال", "مسح الانتحال", "مسح انتحال",
    "حذف الانتحال", "حذف انتحال", "ايقاف الانتحال", "ايقاف انتحال",
    "الغي الانتحال", "الغي انتحال", "رجوع الانتحال", "انهاء الانتحال", "انهاء انتحال",
    "فك الانتحال", "فك انتحال", "استرجاع الحساب", "ارجاع الحساب",
}

async def _download_file_bytes_direct(bot: Bot, file_id: str) -> tuple[bytes, bool]:
    """يحمل ملف الصورة أو الفيديو المتحرك مباشرة من سيرفر تيليجرام عبر HTTP لضمان عمله على كل إصدارات Aiogram."""
    if not file_id:
        return b"", False
    is_video = False
    # المحاولة 1: عبر HTTP المباشر إلى Bot API
    try:
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            api_base = f"https://api.telegram.org/bot{TOKEN}"
            async with session.get(f"{api_base}/getFile", params={"file_id": file_id}) as resp:
                info = await resp.json(content_type=None)
            if info.get("ok") and info.get("result", {}).get("file_path"):
                file_path = info["result"]["file_path"]
                if file_path.lower().endswith((".mp4", ".webm", ".mov")):
                    is_video = True
                file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                async with session.get(file_url) as fresp:
                    if fresp.status == 200:
                        data = await fresp.read()
                        if data:
                            return data, is_video
    except Exception:
        logger.warning("Direct HTTP file download failed, trying bot.get_file fallback", exc_info=True)

    # المحاولة 2: عبر bot.get_file + bot.download_file
    try:
        import io
        f_obj = await bot.get_file(file_id)
        f_path = getattr(f_obj, "file_path", "") or ""
        if f_path.lower().endswith((".mp4", ".webm", ".mov")):
            is_video = True
        buf = io.BytesIO()
        await bot.download_file(f_path, destination=buf)
        data = buf.getvalue()
        if data:
            return data, is_video
    except Exception:
        logger.warning("bot.download_file fallback failed", exc_info=True)
    return b"", is_video

async def _scrape_public_avatar_bytes(username: str) -> bytes:
    """يجلب صورة البروفايل العامة من صفحة t.me/<username> في حال كانت الصور مقفلة في Bot API بسبب الخصوصية."""
    uname = (username or "").strip().lstrip("@")
    if not uname:
        return b""
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"
        }
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(f"https://t.me/{uname}") as resp:
                if resp.status != 200:
                    return b""
                page_html = await resp.text()
            m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', page_html, re.I)
            if not m:
                m = re.search(r'class=["\']tgme_page_photo_image["\'][^>]+src=["\']([^"\']+)["\']', page_html, re.I)
            if not m:
                return b""
            img_url = html.unescape(m.group(1).strip())
            # تجاهل لوجو تيليجرام الافتراضي عندما لا توجد صورة
            if not img_url.startswith("http") or "telegram_logo" in img_url or "tgme/oshi" in img_url:
                return b""
            async with session.get(img_url) as img_resp:
                if img_resp.status == 200:
                    content = await img_resp.read()
                    # لوجو تيليجرام الافتراضي أو الصور الفارغة صغيرة جداً
                    if content and len(content) > 1500:
                        return content
    except Exception:
        logger.warning("Public t.me avatar scrape failed for %s", uname, exc_info=True)
    return b""

def _normalize_jpeg_bytes(raw_bytes: bytes) -> bytes:
    """يتأكد أن الصورة بصيغة JPEG قياسية صالحة لـ setBusinessAccountProfilePhoto."""
    if not raw_bytes:
        return b""
    try:
        import io
        from PIL import Image
        with Image.open(io.BytesIO(raw_bytes)) as im:
            im = im.convert("RGB")
            out = io.BytesIO()
            im.save(out, format="JPEG", quality=95)
            return out.getvalue()
    except Exception:
        return raw_bytes

async def _upload_business_profile_photo_bytes(bot: Bot, connection_id: str, media_bytes: bytes, is_video: bool = False) -> bool:
    """يرفع صورة أو فيديو البروفايل لحساب Telegram Business مباشرة عبر Multipart HTTP لضمان عدم فشل Aiogram."""
    if not media_bytes:
        return False
    if not is_video:
        media_bytes = _normalize_jpeg_bytes(media_bytes)

    url = f"https://api.telegram.org/bot{TOKEN}/setBusinessAccountProfilePhoto"
    timeout = aiohttp.ClientTimeout(total=30)
    field_name = "profile_media"
    photo_payload = (
        {"type": "animated", "animation": f"attach://{field_name}"}
        if is_video
        else {"type": "static", "photo": f"attach://{field_name}"}
    )
    filename = "avatar.mp4" if is_video else "avatar.jpg"
    content_type = "video/mp4" if is_video else "image/jpeg"

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for is_pub in ("true", "false", None):
            try:
                form = aiohttp.FormData()
                form.add_field("business_connection_id", str(connection_id))
                if is_pub is not None:
                    form.add_field("is_public", is_pub)
                form.add_field("photo", json.dumps(photo_payload))
                form.add_field(
                    field_name,
                    media_bytes,
                    filename=filename,
                    content_type=content_type,
                )
                async with session.post(url, data=form) as resp:
                    res = await resp.json(content_type=None)
                if res.get("ok"):
                    return True
                logger.warning("setBusinessAccountProfilePhoto attempt (is_public=%s) response: %s", is_pub, res)
            except Exception:
                logger.warning("setBusinessAccountProfilePhoto HTTP call failed", exc_info=True)

    # محاولة احتياطية عبر دالة Aiogram إن وجدت
    tmp_path = f"imp_photo_{connection_id}_{secrets.token_hex(4)}.{ 'mp4' if is_video else 'jpg' }"
    try:
        with open(tmp_path, "wb") as f:
            f.write(media_bytes)
        from aiogram.types import InputProfilePhotoStatic, InputProfilePhotoAnimated, FSInputFile
        photo_obj = (
            InputProfilePhotoAnimated(type="animated", animation=FSInputFile(tmp_path))
            if is_video
            else InputProfilePhotoStatic(type="static", photo=FSInputFile(tmp_path))
        )
        await bot.set_business_account_profile_photo(
            business_connection_id=connection_id,
            photo=photo_obj,
            is_public=True,
        )
        return True
    except Exception:
        logger.exception("Aiogram fallback for set_business_account_profile_photo also failed")
        return False
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

async def _remove_business_photo(bot: Bot, connection_id: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/removeBusinessAccountProfilePhoto"
    timeout = aiohttp.ClientTimeout(total=20)
    removed_any = False
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for payload in (
            {"business_connection_id": str(connection_id), "is_public": True},
            {"business_connection_id": str(connection_id), "is_public": False},
            {"business_connection_id": str(connection_id)},
        ):
            try:
                async with session.post(url, json=payload) as resp:
                    res = await resp.json(content_type=None)
                if res.get("ok"):
                    removed_any = True
                    break
            except Exception:
                logger.warning("removeBusinessAccountProfilePhoto HTTP attempt failed", exc_info=True)
    if removed_any:
        return True
    try:
        await bot.remove_business_account_profile_photo(
            business_connection_id=connection_id,
            is_public=True,
        )
        return True
    except Exception:
        try:
            await bot.remove_business_account_profile_photo(
                business_connection_id=connection_id,
            )
            return True
        except Exception:
            return False

async def _fetch_user_avatar_info(bot: Bot, user_id: int, username: str = "") -> tuple[str, bytes, bool]:
    """
    يرجع (file_id, raw_bytes, is_video) لصورة المستخدم من كل المصادر المتاحة:
    1. get_user_profile_photos
    2. get_chat(user_id).photo (big_file_id / small_file_id)
    3. جلب الصورة العامة من t.me/<username> إن كانت الصورة مقفلة في Bot API
    """
    candidate_file_ids = []
    try:
        photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
        if photos and photos.total_count and photos.photos:
            for sz in reversed(photos.photos[0]):
                fid = getattr(sz, "file_id", "")
                if fid and fid not in candidate_file_ids:
                    candidate_file_ids.append(fid)
    except Exception:
        logger.warning("get_user_profile_photos failed for %s", user_id, exc_info=True)

    chat_username = username or ""
    try:
        chat = await bot.get_chat(user_id)
        if not chat_username:
            chat_username = getattr(chat, "username", "") or ""
        chat_photo = getattr(chat, "photo", None)
        if chat_photo:
            for attr in ("big_file_id", "small_file_id"):
                fid = getattr(chat_photo, attr, "")
                if fid and fid not in candidate_file_ids:
                    candidate_file_ids.append(fid)
    except Exception:
        logger.warning("get_chat failed for %s", user_id, exc_info=True)

    for fid in candidate_file_ids:
        data, is_video = await _download_file_bytes_direct(bot, fid)
        if data:
            return fid, data, is_video

    # في حال كانت الخصوصية تمنع البوت من رؤية الصورة عبر Bot API ولكن للمستخدم يوزر عام
    if chat_username:
        scraped = await _scrape_public_avatar_bytes(chat_username)
        if scraped:
            return f"scraped:{chat_username}", scraped, False

    return "", b"", False

async def _set_business_photo_from_stored_id(bot: Bot, connection_id: str, stored_id: str, fallback_user_id: int = 0) -> bool:
    if not stored_id and not fallback_user_id:
        return False
    if stored_id.startswith("localfile:"):
        local_path = stored_id[len("localfile:"):]
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    raw = f.read()
                return await _upload_business_profile_photo_bytes(bot, connection_id, raw, is_video=local_path.endswith(".mp4"))
            except Exception:
                pass
    if stored_id.startswith("scraped:"):
        uname = stored_id[len("scraped:"):]
        raw = await _scrape_public_avatar_bytes(uname)
        if raw:
            return await _upload_business_profile_photo_bytes(bot, connection_id, raw, is_video=False)
    if stored_id:
        raw, is_video = await _download_file_bytes_direct(bot, stored_id)
        if raw:
            return await _upload_business_profile_photo_bytes(bot, connection_id, raw, is_video=is_video)
    if fallback_user_id:
        _, raw, is_video = await _fetch_user_avatar_info(bot, fallback_user_id)
        if raw:
            return await _upload_business_profile_photo_bytes(bot, connection_id, raw, is_video=is_video)
    return False

async def perform_impersonation(message: Message, owner_id: int, bc_id: str):
    bot = message.bot
    await delete_biz_msg(bot, bc_id, message.chat.id, message.message_id)
    target_id = message.chat.id
    target_username = getattr(message.chat, "username", "") or ""
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id != owner_id:
        target_id = message.reply_to_message.from_user.id
        target_username = getattr(message.reply_to_message.from_user, "username", "") or target_username

    conn = await db()
    existing_backup = await fetchone(
        conn, "SELECT * FROM impersonation_backups WHERE owner_id=?", (owner_id,)
    )
    biz_row = await fetchone(
        conn,
        "SELECT original_name, original_last_name, clock_enabled FROM business WHERE connection_id=?",
        (bc_id,),
    )
    settings_row = await fetchone(
        conn,
        "SELECT live_bio_enabled FROM settings WHERE owner_id=?",
        (owner_id,),
    )

    if not existing_backup or not existing_backup["active"]:
        orig_first = ""
        orig_last = ""
        orig_bio = ""
        owner_username = ""
        try:
            owner_chat = await bot.get_chat(owner_id)
            orig_first = getattr(owner_chat, "first_name", "") or ""
            orig_last = getattr(owner_chat, "last_name", "") or ""
            orig_bio = getattr(owner_chat, "bio", "") or ""
            owner_username = getattr(owner_chat, "username", "") or ""
        except Exception:
            logger.warning("Could not fetch owner chat info before impersonation", exc_info=True)

        if biz_row and biz_row["clock_enabled"]:
            orig_first = clean_clock_suffix(biz_row["original_name"] or orig_first) or orig_first
            orig_last = biz_row["original_last_name"] if biz_row["original_last_name"] is not None else ""
        else:
            if not orig_first and biz_row:
                orig_first = biz_row["original_name"] or ""
            if not orig_last and biz_row and biz_row["original_last_name"]:
                orig_last = biz_row["original_last_name"] or ""

        orig_fid, orig_bytes, orig_is_video = await _fetch_user_avatar_info(bot, owner_id, owner_username)
        orig_photo_ref = orig_fid
        if orig_bytes:
            ext = "mp4" if orig_is_video else "jpg"
            backup_file_path = f"imp_orig_owner_{owner_id}.{ext}"
            try:
                with open(backup_file_path, "wb") as bf:
                    bf.write(orig_bytes if orig_is_video else _normalize_jpeg_bytes(orig_bytes))
                orig_photo_ref = f"localfile:{backup_file_path}"
            except Exception:
                logger.warning("Could not save local owner photo backup", exc_info=True)

        clock_was = int(bool(biz_row and biz_row["clock_enabled"]))
        bio_was = int(bool(settings_row and settings_row["live_bio_enabled"]))

        await conn.execute(
            """
            INSERT INTO impersonation_backups(
                owner_id, connection_id, first_name, last_name, bio,
                photo_file_id, clock_was_enabled, live_bio_was_enabled,
                active, target_id, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(owner_id) DO UPDATE SET
                connection_id=excluded.connection_id,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                bio=excluded.bio,
                photo_file_id=excluded.photo_file_id,
                clock_was_enabled=excluded.clock_was_enabled,
                live_bio_was_enabled=excluded.live_bio_was_enabled,
                active=1,
                target_id=excluded.target_id,
                updated_at=excluded.updated_at
            """,
            (
                owner_id, bc_id, orig_first, orig_last, orig_bio,
                orig_photo_ref, clock_was, bio_was, target_id,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    else:
        await conn.execute(
            "UPDATE impersonation_backups SET target_id=?, connection_id=?, updated_at=? WHERE owner_id=?",
            (target_id, bc_id, datetime.now(timezone.utc).isoformat(), owner_id),
        )

    await conn.execute("UPDATE business SET clock_enabled=0 WHERE user_id=?", (owner_id,))
    await conn.execute("UPDATE settings SET live_bio_enabled=0 WHERE owner_id=?", (owner_id,))
    await conn.commit()
    await conn.close()

    target_first = getattr(message.chat, "first_name", "") or ""
    target_last = getattr(message.chat, "last_name", "") or ""
    target_bio = ""
    try:
        target_chat = await bot.get_chat(target_id)
        target_first = getattr(target_chat, "first_name", None) or target_first
        target_last = getattr(target_chat, "last_name", None) if getattr(target_chat, "last_name", None) is not None else target_last
        target_bio = getattr(target_chat, "bio", None) or ""
        if not target_username:
            target_username = getattr(target_chat, "username", "") or ""
    except Exception:
        logger.warning("Could not fetch target chat details for %s", target_id, exc_info=True)

    target_first = (target_first or " ").strip()[:64] or " "
    target_last = (target_last or "").strip()[:64]

    await set_business_name(bot, bc_id, target_first, target_last)
    await set_business_bio(bot, bc_id, target_bio)

    _, target_photo_bytes, target_is_video = await _fetch_user_avatar_info(bot, target_id, target_username)
    if target_photo_bytes:
        await _upload_business_profile_photo_bytes(bot, bc_id, target_photo_bytes, is_video=target_is_video)
    else:
        await _remove_business_photo(bot, bc_id)

async def restore_impersonation(message: Message, owner_id: int, bc_id: str):
    bot = message.bot
    await delete_biz_msg(bot, bc_id, message.chat.id, message.message_id)
    conn = await db()
    backup = await fetchone(
        conn, "SELECT * FROM impersonation_backups WHERE owner_id=?", (owner_id,)
    )
    biz_row = await fetchone(
        conn, "SELECT original_name, original_last_name, clock_style FROM business WHERE connection_id=?", (bc_id,)
    )

    if backup:
        orig_first = (backup["first_name"] or (biz_row["original_name"] if biz_row else "") or " ").strip()[:64] or " "
        orig_last = (backup["last_name"] if backup["last_name"] is not None else (biz_row["original_last_name"] if biz_row and biz_row["original_last_name"] is not None else "")).strip()[:64]
        orig_bio = backup["bio"] or ""
        orig_photo_id = backup["photo_file_id"] or ""
        clock_was = int(bool(backup["clock_was_enabled"]))
        bio_was = int(bool(backup["live_bio_was_enabled"]))
        await conn.execute("UPDATE impersonation_backups SET active=0, updated_at=? WHERE owner_id=?", (datetime.now(timezone.utc).isoformat(), owner_id))
    else:
        orig_first = ((biz_row["original_name"] if biz_row else "") or " ").strip()[:64] or " "
        orig_last = ((biz_row["original_last_name"] if biz_row and biz_row["original_last_name"] is not None else "")).strip()[:64]
        orig_bio = ""
        orig_photo_id = ""
        clock_was = 0
        bio_was = 0

    if clock_was:
        await conn.execute("UPDATE business SET clock_enabled=1 WHERE connection_id=?", (bc_id,))
    if bio_was:
        await conn.execute("UPDATE settings SET live_bio_enabled=1 WHERE owner_id=?", (owner_id,))
    await conn.commit()
    await conn.close()

    # حذف صورة الحساب المنتحل أولاً ثم إرجاع الصورة الأساسية والاسم والبايو
    await _remove_business_photo(bot, bc_id)
    if orig_photo_id:
        await _set_business_photo_from_stored_id(bot, bc_id, orig_photo_id, fallback_user_id=0)

    style = int(biz_row["clock_style"] if biz_row and biz_row["clock_style"] is not None else 0)
    final_last = clock_text(style) if clock_was else orig_last
    await set_business_name(bot, bc_id, orig_first, final_last)
    await set_business_bio(bot, bc_id, orig_bio)
    if bio_was:
        try:
            await apply_live_bio(bot, owner_id, advance=False, connection_id=bc_id)
        except Exception:
            pass

@router.business_message()
async def business_message(message: Message):
    bc_id = message.business_connection_id
    if not bc_id or not message.chat:
        return

    # دعم أمر Truecaller داخل محادثات Telegram Business
    if message.text and message.text.split(maxsplit=1)[0].split("@")[0].lower() == "/tc":
        conn = await db()
        biz = await fetchone(conn, "SELECT user_id, enabled FROM business WHERE connection_id=?", (bc_id,))
        await conn.close()
        if not biz:
            biz = await recover_business_connection(message.bot, bc_id)
        if not biz or not biz["enabled"]:
            return
        if not await paid_access_allowed(biz["user_id"]):
            return
        await _handle_truecaller_command(message, business_connection_id=bc_id)
        return

    conn = await db()
    biz = await fetchone(conn,
        "SELECT user_id, enabled, can_reply FROM business WHERE connection_id=?", (bc_id,))
    if not biz:
        await conn.close()
        biz = await recover_business_connection(message.bot, bc_id)
        if not biz:
            logger.warning("business_message ignored: unknown business connection %s", bc_id)
            return
        conn = await db()

    if not biz["enabled"]:
        logger.info("business_message ignored: connection %s is disabled", bc_id)
        await conn.close()
        return
    if not await paid_access_allowed(biz["user_id"]):
        logger.info("business_message ignored: no active access for user %s", biz["user_id"])
        await conn.close()
        return
    tracked_text = message.html_text or message.text or message.caption or ""
    tracked_media_type = ""
    tracked_media_file_id = ""
    if message.photo:
        tracked_media_type = "photo"
        tracked_media_file_id = message.photo[-1].file_id
    elif message.video:
        tracked_media_type = "video"
        tracked_media_file_id = message.video.file_id
    elif message.voice:
        tracked_media_type = "voice"
        tracked_media_file_id = message.voice.file_id
    elif message.audio:
        tracked_media_type = "audio"
        tracked_media_file_id = message.audio.file_id
    elif message.document:
        tracked_media_type = "document"
        tracked_media_file_id = message.document.file_id
    elif message.animation:
        tracked_media_type = "animation"
        tracked_media_file_id = message.animation.file_id
    elif message.sticker:
        tracked_media_type = "sticker"
        tracked_media_file_id = message.sticker.file_id
    await conn.execute("""
        INSERT OR REPLACE INTO tracked_messages(
            connection_id, chat_id, message_id, sender_id,
            sender_name, sender_username, text_content,
            media_type, media_file_id, created_at
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bc_id, message.chat.id, message.message_id,
        message.from_user.id if message.from_user else message.chat.id,
        message.from_user.first_name if message.from_user else "",
        message.from_user.username if message.from_user else "",
        tracked_text, tracked_media_type, tracked_media_file_id,
        datetime.now(timezone.utc).isoformat()
    ))
    await conn.commit()

    text_raw = message.text or message.caption or ""
    text = text_raw.lower().strip()
    customer_exists = await fetchone(conn, "SELECT 1 FROM customers WHERE connection_id=? AND chat_id=?", (bc_id, message.chat.id))
    await conn.execute("""
        INSERT INTO customers(connection_id, chat_id, first_name, username, last_seen)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(connection_id, chat_id) DO UPDATE SET
        first_name=excluded.first_name,
        username=excluded.username,
        last_seen=excluded.last_seen
    """, (
        bc_id, message.chat.id, message.chat.first_name or "",
        message.chat.username or "", datetime.now(timezone.utc).isoformat()
    ))
    await conn.commit()
    transfer_request = parse_transfer_request(text_raw) if (await get_account_setting(biz["user_id"], "transfer_enabled")) else None
    if transfer_request:
        phone, amount = transfer_request
        await conn.close()
        try:
            await send_transfer_codes(message, phone, amount, business_connection_id=bc_id)
        except Exception:
            logger.exception("Failed to send transfer codes")
        return

    account_owner_id = biz["user_id"]
    is_account_owner_chat = message.chat.id == account_owner_id
    is_owner_message = bool(message.from_user and message.from_user.id == account_owner_id) or is_account_owner_chat
    is_mute_protected = bool(
        message.chat.id in PROTECTED_MUTE_USER_ID_SET
        or (message.from_user and message.from_user.id in PROTECTED_MUTE_USER_ID_SET)
    )
    vip_customer = False if is_owner_message else await is_vip_customer_chat(bc_id, message.chat.id)
    owner_command = (text or "").strip().lstrip("/")
    if is_owner_message and owner_command in {"حسابي", "id", "ايدي", "آيدي"}:
        target_user_id = account_owner_id if owner_command == "حسابي" else message.chat.id
        fallback_name = ""
        fallback_username = ""
        if target_user_id == message.chat.id:
            fallback_name = (
                getattr(message.chat, "full_name", None)
                or getattr(message.chat, "first_name", None)
                or ""
            )
            fallback_username = getattr(message.chat, "username", None) or ""
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        await conn.close()
        try:
            await send_profile_card(message, target_user_id, fallback_name, fallback_username)
        except Exception:
            logger.exception("Failed to send profile card for %s", target_user_id)
        return

    muted = await fetchone(conn,
        "SELECT 1 FROM muted WHERE connection_id=? AND chat_id=?", (bc_id, message.chat.id))
    if muted and (await get_account_setting(biz["user_id"], "muted_enabled") if await get_account_setting(biz["user_id"], "muted_enabled") is not None else 1) and not is_owner_message and not is_mute_protected:
        await conn.close()
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        return

    if is_owner_message and message.reply_to_message and text_raw.strip() == "تثبيت":
        await conn.close()
        try:
            await message.bot.pin_chat_message(
                chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id,
                business_connection_id=bc_id,
                disable_notification=True,
            )
        except Exception:
            logger.warning("Failed to pin message", exc_info=True)
            return
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        return
    if is_owner_message and text_raw and await maybe_translate_outgoing(message, bc_id):
        await conn.close()
        return
    if text_raw and await maybe_start_calculator(message, account_owner_id, bc_id):
        await conn.close()
        return
    if text_raw and await maybe_start_song(message, bc_id):
        await conn.close()
        return
    if text_raw and await maybe_start_xo(message, account_owner_id, bc_id, is_owner_message):
        await conn.close()
        return
    if not is_owner_message and text_raw:
        spawn(send_translation_card(message.bot, account_owner_id, message))
        spawn(send_link_alert(message.bot, account_owner_id, message))

    settings = await fetchone(conn,
        "SELECT enabled, welcome, welcome_enabled, welcome_mode, welcome_sticker_file_id, welcome_image_file_id, welcome_image_type FROM settings WHERE owner_id=?",
        (account_owner_id,))
    if not settings or not settings["enabled"]:
        await conn.close()
        return
    try:
        delete_types = set(json.loads(await get_account_setting(biz["user_id"], "media_delete_types") or "[]"))
    except Exception:
        delete_types = set()
    incoming_type = tracked_media_type or ("text" if (message.text or message.caption) else "")
    if (not is_owner_message and not vip_customer and await get_account_setting(biz["user_id"], "media_enabled")) and incoming_type in delete_types:
        await conn.close()
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        return

    customer_user_id = message.from_user.id if message.from_user else message.chat.id

    previous_prompt = await fetchone(conn, "SELECT last_subscription_prompt_id FROM customers WHERE connection_id=? AND chat_id=?", (bc_id, message.chat.id))
    previous_prompt_id = previous_prompt["last_subscription_prompt_id"] if previous_prompt else 0

    missing = [] if is_owner_message or vip_customer or not (await get_account_setting(account_owner_id, "account_force_enabled") if await get_account_setting(account_owner_id, "account_force_enabled") is not None else 1) else await required_subs(message.bot, customer_user_id, account_owner_id, scope="account")
    if missing:
        await conn.close()
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        subscription_text = await get_account_message(account_owner_id, "account_force_sub")
        try:
            if previous_prompt_id:
                await delete_biz_msg(message.bot, bc_id, message.chat.id, previous_prompt_id)
            sent_prompt = await message.bot.send_message(
                chat_id=message.chat.id,
                text=subscription_text,
                reply_markup=sub_kb(missing),
                business_connection_id=bc_id,
                parse_mode="HTML",
            )
            await conn2_update_subscription_prompt(bc_id, message.chat.id, sent_prompt.message_id)
        except Exception:
            logger.exception("Failed to send mandatory-subscription prompt")
        return

    if previous_prompt_id:
        await delete_biz_msg(message.bot, bc_id, message.chat.id, previous_prompt_id)
        await conn.execute("UPDATE customers SET last_subscription_prompt_id=0 WHERE connection_id=? AND chat_id=?", (bc_id, message.chat.id))
        await conn.commit()

    command_text = re.sub(r"[\s.!؟!?،؛:]+$", "", text).strip()
    norm_imp_cmd = _normalize_impersonate_cmd(text_raw)
    if is_owner_message and norm_imp_cmd in _IMPERSONATE_START_CMDS:
        await conn.close()
        await perform_impersonation(message, account_owner_id, bc_id)
        return
    if is_owner_message and norm_imp_cmd in _IMPERSONATE_STOP_CMDS:
        await conn.close()
        await restore_impersonation(message, account_owner_id, bc_id)
        return
    if is_owner_message and command_text in {"كتم"}:
        if is_mute_protected:
            await conn.close()
            await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
            try:
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text="هذا الحساب محمي ولا يمكن كتمه.",
                    business_connection_id=bc_id
                )
            except Exception:
                pass
            return
        await conn.execute(
            "INSERT OR IGNORE INTO muted(connection_id, chat_id) VALUES(?, ?)",
            (bc_id, message.chat.id))
        await conn.commit()
        await conn.close()
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        try:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text="تم كتم العميل.",
                business_connection_id=bc_id
            )
        except Exception:
            pass
        return

    if is_owner_message and command_text in {"الغاء الكتم", "إلغاء الكتم"}:
        await conn.execute(
            "DELETE FROM muted WHERE connection_id=? AND chat_id=?",
            (bc_id, message.chat.id))
        await conn.commit()
        await conn.close()
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        try:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text="تم إلغاء كتم العميل.",
                business_connection_id=bc_id
            )
        except Exception:
            pass
        return

    if text and not is_owner_message and not is_mute_protected and not vip_customer:
        banned = await conn.execute_fetchall(
            "SELECT word FROM banned_words WHERE owner_id=?", (account_owner_id,))
        matched_word = next((row["word"] for row in banned if re.search(r"(?<!\w)" + re.escape(row["word"].lower()) + r"(?!\w)", text)), None)
        if matched_word:
            now_iso = datetime.now(timezone.utc).isoformat()
            await conn.execute("""INSERT INTO violations(connection_id, chat_id, owner_id, count, last_word, updated_at)
                VALUES(?, ?, ?, 1, ?, ?) ON CONFLICT(connection_id, chat_id) DO UPDATE SET
                count=count+1, last_word=excluded.last_word, updated_at=excluded.updated_at""",
                (bc_id, message.chat.id, account_owner_id, matched_word, now_iso))
            violation = await fetchone(conn, "SELECT count FROM violations WHERE connection_id=? AND chat_id=?", (bc_id, message.chat.id))
            count = violation["count"]
            await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
            if count >= 4:
                await conn.execute("INSERT OR IGNORE INTO muted(connection_id, chat_id) VALUES(?, ?)", (bc_id, message.chat.id))
                await conn.commit(); await conn.close()
                notice = "<blockquote><tg-emoji emoji-id='6206110936789423908'>🔇</tg-emoji> <b>تم تفعيل الكتم التلقائي</b>\nتكرر استخدام كلمة ممنوعة 4 مرات.</blockquote>"
            else:
                await conn.commit(); await conn.close()
                notice = f"<blockquote><tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> <b>تنبيه رقم {count}/4</b>\nهذه الكلمة غير مسموح بها.</blockquote>"
            try:
                await message.bot.send_message(chat_id=message.chat.id, text=notice, business_connection_id=bc_id)
            except Exception:
                pass
            return

    if is_owner_message and normalize_payment_phrase(text_raw) in {normalize_payment_phrase("طرق دفعي"), normalize_payment_phrase("طرق الدفع")}:
        wallets = []
        for key in PAYMENT_METHODS:
            wallet = await get_payment_wallet(account_owner_id, key)
            if wallet and wallet["enabled"] and wallet["wallet_value"]:
                wallets.append(key)
        await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
        await conn.close()
        if wallets:
            buttons=[]
            for key in wallets:
                info=PAYMENT_METHODS[key]
                buttons.append([InlineKeyboardButton(text=info["name"], callback_data=f"bpay_{key}", style="primary", icon_custom_emoji_id=info["emoji"])])
            await message.bot.send_message(chat_id=message.chat.id, text="<b>طرق الدفع المتاحة</b>\n\nاختر الطريقة المطلوبة:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), business_connection_id=bc_id, parse_mode="HTML")
        else:
            await message.bot.send_message(chat_id=message.chat.id, text="لا توجد طرق دفع مضافة حالياً.", business_connection_id=bc_id)
        return
    payment_key = match_payment_method(text_raw) if is_owner_message and (await get_account_setting(account_owner_id, "payment_enabled") if await get_account_setting(account_owner_id, "payment_enabled") is not None else 1) else None
    if payment_key:
        wallet = await get_payment_wallet(account_owner_id, payment_key)
        if wallet and wallet["enabled"] and wallet["wallet_value"]:
            await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
            await conn.close()
            try:
                await send_payment_details(message, payment_key, wallet, business_connection_id=bc_id)
            except Exception:
                logger.exception("Failed to send payment wallet details")
            return

    if text and text in {"تيك توك", "تيكتوك", "انستقرام", "انستجرام", "تليجرام", "فيسبوك", "يوتيوب"} and (await get_account_setting(account_owner_id, "social_enabled")):
        platform_map={"تيك توك":"tiktok","تيكتوك":"tiktok","انستقرام":"instagram","انستجرام":"instagram","تليجرام":"telegram","فيسبوك":"facebook","يوتيوب":"youtube"}
        key=platform_map[text]; link=await get_account_setting(account_owner_id, "social_"+key)
        if link:
            await conn.close()
            icons={"tiktok":"5426903221031414307","instagram":"5429308145019136708","telegram":"5426990524831642021","facebook":"5429591007270283448","youtube":"5427158904729513162"}
            await message.bot.send_message(chat_id=message.chat.id, text=f"رابط حساب {text}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, url=link, style="primary", icon_custom_emoji_id=icons[key])]]), business_connection_id=bc_id)
            return
    currency_request = parse_currency_request(text_raw) if (await get_account_setting(account_owner_id, "currency_enabled")) else None
    if currency_request:
        amount, requested = currency_request
        prices = await fetch_live_prices()
        if prices:
            values = currency_prices_text(amount, requested, prices)
            await conn.close()
            await message.bot.send_message(chat_id=message.chat.id, text=currency_header(amount, requested), reply_markup=currency_keyboard(values, requested), business_connection_id=bc_id, parse_mode="HTML")
            return
        await conn.close()
        try:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text="تعذر جلب سعر العملة الآن. حاول مرة أخرى بعد قليل.",
                business_connection_id=bc_id,
            )
        except Exception:
            logger.warning("Could not report currency price fetch failure", exc_info=True)
        return

    calc_result = try_calculate(text_raw) if (await get_account_setting(account_owner_id, "calculator_enabled")) else None
    if calc_result:
        await conn.close()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="نسخ الإجابة",
                copy_text=CopyTextButton(text=calc_result),
                style="primary"
            )]
        ])
        try:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text=f"<b>{safe_html(calc_result)}</b>",
                reply_markup=kb,
                business_connection_id=bc_id,
                parse_mode="HTML"
            )
        except Exception:
            pass
        return


    if text and (await get_account_setting(account_owner_id, "replies_enabled") if await get_account_setting(account_owner_id, "replies_enabled") is not None else 1):
        replies = await conn.execute_fetchall(
            "SELECT id, trigger, response FROM replies "
            "WHERE owner_id=? ORDER BY id ASC",
            (account_owner_id,))
        for row in replies:
            if text == row["trigger"].lower().strip():
                await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
                btns = await conn.execute_fetchall(
                    "SELECT id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value FROM reply_buttons "
                    "WHERE reply_id=? ORDER BY position", (row["id"],))
                await conn.close()


                ikb = build_reply_kb(btns)

                try:
                    if ikb:
                        await message.bot.send_message(
                            chat_id=message.chat.id,
                            text=row["response"],
                            reply_markup=ikb,
                            business_connection_id=bc_id,
                            parse_mode="HTML"
                        )
                    else:
                        await message.bot.send_message(
                            chat_id=message.chat.id,
                            text=row["response"],
                            business_connection_id=bc_id,
                            parse_mode="HTML"
                        )
                except Exception:
                    logger.exception("Failed to send automatic reply for trigger %s", row["trigger"])
                    try:
                        fallback_kb = build_reply_kb(btns, use_icons=False, use_copy_buttons=False)
                        await message.bot.send_message(
                            chat_id=message.chat.id,
                            text=row["response"],
                            reply_markup=fallback_kb,
                            business_connection_id=bc_id,
                            parse_mode="HTML"
                        )
                    except Exception:
                        logger.exception("Failed to send automatic reply text")
                return


    welcome = settings["welcome"] if settings["welcome_enabled"] else ""
    welcome_sticker_id = settings["welcome_sticker_file_id"] if settings["welcome_enabled"] else ""
    welcome_image_id = settings["welcome_image_file_id"] if settings["welcome_enabled"] else ""
    welcome_buttons_raw = await get_account_setting(account_owner_id, "welcome_buttons") if settings["welcome_enabled"] else "[]"
    try:
        welcome_buttons_data = json.loads(welcome_buttons_raw or "[]")
    except Exception:
        welcome_buttons_data = []
    welcome_markup = welcome_buttons_kb(welcome_buttons_data, account_owner_id)
  
    media_id = ""
    media_type = ""

    sender_is_owner = bool(message.from_user and message.from_user.id == account_owner_id)
    if (welcome or welcome_sticker_id or welcome_image_id) and not sender_is_owner and not vip_customer:
    
        owner_is_recently_active = False
        if settings["welcome_mode"] == "offline":
            owner_last = await fetchone(
                conn,
                "SELECT created_at FROM tracked_messages "
                "WHERE connection_id=? AND sender_id=? "
                "ORDER BY created_at DESC LIMIT 1",
                (bc_id, account_owner_id),
            )
            if owner_last and owner_last["created_at"]:
                try:
                    owner_last_dt = datetime.fromisoformat(owner_last["created_at"])
                    owner_is_recently_active = (datetime.now(timezone.utc) - owner_last_dt) < timedelta(minutes=5)
                except Exception:
                    owner_is_recently_active = False
        cust = await fetchone(conn,
            "SELECT last_welcome FROM customers WHERE connection_id=? AND chat_id=?",
            (bc_id, message.chat.id))
        now = datetime.now(timezone.utc)
        last = cust["last_welcome"] if cust and cust["last_welcome"] else ""
        can_send = True
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if now - last_dt < WELCOME_COOLDOWN:
                    can_send = False
            except Exception:
                pass

        if can_send and not owner_is_recently_active:
            await conn.execute(
                "UPDATE customers SET last_welcome=? WHERE connection_id=? AND chat_id=?",
                (now.isoformat(), bc_id, message.chat.id))
            await conn.commit()
            await conn.close()
            try:
                if welcome_image_id:
                    await message.bot.send_photo(chat_id=message.chat.id, photo=welcome_image_id, caption=welcome or None, reply_markup=welcome_markup, business_connection_id=bc_id, parse_mode="HTML")
                elif media_id and media_type == "photo":
                    await message.bot.send_photo(
                        chat_id=message.chat.id, photo=media_id,
                        caption=welcome or None, business_connection_id=bc_id,
                        parse_mode="HTML"
                    )
                elif media_id and media_type == "video":
                    await message.bot.send_video(
                        chat_id=message.chat.id, video=media_id,
                        caption=welcome or None, business_connection_id=bc_id,
                        parse_mode="HTML"
                    )
                elif welcome:
                    await message.bot.send_message(
                        chat_id=message.chat.id, text=welcome,
                        reply_markup=welcome_markup, business_connection_id=bc_id, parse_mode="HTML"
                    )
                if welcome_sticker_id:
                    await message.bot.send_sticker(
                        chat_id=message.chat.id, sticker=welcome_sticker_id,
                        business_connection_id=bc_id
                    )
            except Exception:
                pass
            return

    await conn.close()

# ───────── زر «تحقق من الاشتراك» للاشتراك الإجباري الخاص بحساب Telegram Business ─────────
_ACCOUNT_VERIFY_INFLIGHT = set()

async def account_required_subs_strict(bot, user_id, owner_id):
    """نفس منطق required_subs لنطاق الحساب، لكن أي تعذّر في قراءة العضوية يُحتسب «غير مشترك»."""
    conn = await db()
    try:
        rows = await conn.execute_fetchall(
            "SELECT channel, title FROM force_channels WHERE owner_id=? AND scope=? ORDER BY id",
            (owner_id, "account")
        )
    finally:
        await conn.close()
    missing = []
    for row in rows:
        try:
            member = await bot.get_chat_member(chat_id=row["channel"], user_id=user_id)
            raw_status = getattr(member, "status", "")
            status = str(getattr(raw_status, "value", raw_status))
            joined = status in {"creator", "administrator", "member"} or (
                status == "restricted" and bool(getattr(member, "is_member", False))
            )
            if not joined:
                missing.append((row["channel"], row["title"]))
        except Exception:
            logger.warning("Could not verify required channel %s (treated as not subscribed)", row["channel"], exc_info=True)
            missing.append((row["channel"], row["title"]))
    return missing

@router.callback_query(F.data == "account_force_verify")
async def account_force_verify(call: CallbackQuery):
    msg = call.message
    bc_id = getattr(msg, "business_connection_id", None)
    chat = getattr(msg, "chat", None)
    if not bc_id or not chat or not call.from_user:
        try:
            await call.answer("انتهت صلاحية هذا الزر، أرسل رسالتك مرة أخرى.", show_alert=True)
        except Exception:
            pass
        return
    chat_id = chat.id
    conn = await db()
    try:
        biz = await fetchone(conn, "SELECT user_id, enabled FROM business WHERE connection_id=?", (bc_id,))
    finally:
        await conn.close()
    if not biz or not biz["enabled"]:
        await call.answer()
        return
    account_owner_id = biz["user_id"]
    if call.from_user.id == account_owner_id or not await paid_access_allowed(account_owner_id):
        await call.answer()
        return

    key = (bc_id, chat_id)
    if key in _ACCOUNT_VERIFY_INFLIGHT:
        await call.answer()
        return
    _ACCOUNT_VERIFY_INFLIGHT.add(key)
    try:
        vip_chat = await is_vip_customer_chat(bc_id, chat_id)
        force_value = await get_account_setting(account_owner_id, "account_force_enabled")
        if not vip_chat and (force_value if force_value is not None else 1):
            missing = await account_required_subs_strict(call.bot, call.from_user.id, account_owner_id)
            if missing:
                try:
                    await call.answer("لم يكتمل اشتراكك في كل القنوات المطلوبة. اشترك ثم اضغط «تحقق من الاشتراك» مرة أخرى.", show_alert=True)
                except Exception:
                    pass
                return
        try:
            await call.answer("تم التحقق من اشتراكك بنجاح.")
        except Exception:
            pass

        # إزالة رسالة الاشتراك (أو على الأقل زرها) حتى لا يتكرر الضغط
        try:
            await call.bot.delete_business_messages(business_connection_id=bc_id, message_ids=[msg.message_id])
        except Exception:
            logger.warning("Failed to delete subscription prompt after verification", exc_info=True)
            try:
                await call.bot.edit_message_reply_markup(
                    business_connection_id=bc_id, chat_id=chat_id,
                    message_id=msg.message_id, reply_markup=None
                )
            except Exception:
                pass
        conn = await db()
        try:
            await conn.execute("UPDATE customers SET last_subscription_prompt_id=0 WHERE connection_id=? AND chat_id=?", (bc_id, chat_id))
            await conn.commit()
        finally:
            await conn.close()

        # رسالة الترحيب: نفس الإعدادات والمحتوى والأزرار ونفس شروط الإرسال (الوضع + فترة الانتظار) في business_message
        conn = await db()
        try:
            settings = await fetchone(conn,
                "SELECT enabled, welcome, welcome_enabled, welcome_mode, welcome_sticker_file_id, welcome_image_file_id FROM settings WHERE owner_id=?",
                (account_owner_id,))
            if vip_chat or not settings or not settings["enabled"] or not settings["welcome_enabled"]:
                return
            welcome = settings["welcome"] or ""
            welcome_sticker_id = settings["welcome_sticker_file_id"] or ""
            welcome_image_id = settings["welcome_image_file_id"] or ""
            if not (welcome or welcome_sticker_id or welcome_image_id):
                return
            if settings["welcome_mode"] == "offline":
                owner_last = await fetchone(
                    conn,
                    "SELECT created_at FROM tracked_messages "
                    "WHERE connection_id=? AND sender_id=? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (bc_id, account_owner_id),
                )
                if owner_last and owner_last["created_at"]:
                    try:
                        owner_last_dt = datetime.fromisoformat(owner_last["created_at"])
                        if (datetime.now(timezone.utc) - owner_last_dt) < timedelta(minutes=5):
                            return
                    except Exception:
                        pass
            cust = await fetchone(conn,
                "SELECT last_welcome FROM customers WHERE connection_id=? AND chat_id=?",
                (bc_id, chat_id))
            now = datetime.now(timezone.utc)
            last = cust["last_welcome"] if cust and cust["last_welcome"] else ""
            if last:
                try:
                    if now - datetime.fromisoformat(last) < WELCOME_COOLDOWN:
                        return
                except Exception:
                    pass
            await conn.execute(
                "UPDATE customers SET last_welcome=? WHERE connection_id=? AND chat_id=?",
                (now.isoformat(), bc_id, chat_id))
            await conn.commit()
        finally:
            await conn.close()

        welcome_buttons_raw = await get_account_setting(account_owner_id, "welcome_buttons")
        try:
            welcome_buttons_data = json.loads(welcome_buttons_raw or "[]")
        except Exception:
            welcome_buttons_data = []
        welcome_markup = welcome_buttons_kb(welcome_buttons_data, account_owner_id)
        try:
            if welcome_image_id:
                await call.bot.send_photo(chat_id=chat_id, photo=welcome_image_id, caption=welcome or None, reply_markup=welcome_markup, business_connection_id=bc_id, parse_mode="HTML")
            elif welcome:
                await call.bot.send_message(chat_id=chat_id, text=welcome, reply_markup=welcome_markup, business_connection_id=bc_id, parse_mode="HTML")
            if welcome_sticker_id:
                await call.bot.send_sticker(chat_id=chat_id, sticker=welcome_sticker_id, business_connection_id=bc_id)
        except Exception:
            logger.exception("Failed to send welcome message after subscription verification")
    finally:
        _ACCOUNT_VERIFY_INFLIGHT.discard(key)

@router.callback_query(F.data == "welcome_image")
async def welcome_image(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(WelcomeSG.set_image)
    await call.message.edit_text("<b>إضافة صورة الترحيب</b>\n\nأرسل صورة الآن.", reply_markup=cancel_kb("advanced"), parse_mode="HTML")
    await call.answer()

@router.message(WelcomeSG.set_image)
async def welcome_image_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if not message.photo:
        await message.answer("<tg-emoji emoji-id='6206110936789423908'>⚠️</tg-emoji> من فضلك أرسل صورة فقط.")
        return
    owner=await settings_owner(message.from_user.id)
    await set_account_setting(owner, "welcome_image_file_id", message.photo[-1].file_id)
    await set_account_setting(owner, "welcome_image_type", "photo")
    await state.set_state(WelcomeSG.ask_mode)
    await message.answer("تم حفظ الصورة. اختر حالة إرسال الترحيب:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="دائماً", callback_data="welcome_mode_always", style="primary"), InlineKeyboardButton(text="عند عدم الاتصال فقط", callback_data="welcome_mode_offline", style="primary")]]), parse_mode="HTML")

@router.callback_query(F.data == "welcome_image_delete")
async def welcome_image_delete(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    await set_account_setting(owner, "welcome_image_file_id", "")
    await set_account_setting(owner, "welcome_image_type", "")
    conn = await db(); row = await fetchone(conn, "SELECT welcome_enabled, welcome_mode FROM settings WHERE owner_id=?", (owner,)); await conn.close()
    await call.answer("تم حذف صورة الترحيب")
    await call.message.edit_text("تم حذف صورة الترحيب بنجاح.", reply_markup=back_kb("welcome"), parse_mode="HTML")

@router.callback_query(F.data == "welcome_sticker_delete")
async def welcome_sticker_delete(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    owner = await settings_owner(call.from_user.id)
    await set_account_setting(owner, "welcome_sticker_file_id", "")
    conn = await db(); row = await fetchone(conn, "SELECT welcome_enabled, welcome_mode FROM settings WHERE owner_id=?", (owner,)); await conn.close()
    await call.answer("تم حذف ملصق الترحيب")
    await call.message.edit_text("تم حذف ملصق الترحيب بنجاح.", reply_markup=back_kb("welcome"), parse_mode="HTML")

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def tracking_identity(name, username, sender_id):
    username_text = f"@{safe_html(username)}" if username else "غير متوفر"
    return (
        f"<tg-emoji emoji-id='5778145208411624388'>👤</tg-emoji> الاسم: {safe_html(name) or 'غير معروف'}\n"
        f"<tg-emoji emoji-id='6028171274939797252'>🔗</tg-emoji> اليوزر: {username_text}\n"
        f"<tg-emoji emoji-id='5891207662678317861'>👤</tg-emoji> آيدي: <code>{sender_id}</code>"
    )


MEDIA_TYPE_LABELS = {
    "photo": "صورة",
    "sticker": "ملصق",
    "video": "فيديو",
    "voice": "رسالة صوتية",
    "audio": "ملف صوتي",
    "document": "ملف",
    "animation": "رسالة متحركة",
}


def tracked_message_display(text_content, media_type):
    label = MEDIA_TYPE_LABELS.get(media_type or "")
    text_content = text_content or ""
    if label and text_content:
        return f"{label}\nالنص المرفق: {text_content}"
    if label:
        return label
    return text_content or "(بدون نص)"


# ═══════════════════════════════════════════════════════════════════════════
# ميزات إضافية: مركز الشرح / الإعدادات المتقدمة / الترجمة وكارت العميل /
# لعبة XO / الرسائل المجدولة
# ═══════════════════════════════════════════════════════════════════════════
import secrets
import aiohttp

try:
    from zoneinfo import ZoneInfo
    BOT_TZ = ZoneInfo(os.getenv("BOT_TIMEZONE", "Africa/Cairo"))
except Exception:
    BOT_TZ = timezone(timedelta(hours=3))

_BG_TASKS = set()

def spawn(coro):
    """تشغيل مهمة في الخلفية مع الاحتفاظ بمرجعها حتى لا تُحذف قبل انتهائها."""
    task = asyncio.create_task(coro)
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)
    return task


async def init_extra_features():
    conn = await db()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                connection_id TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                customer_name TEXT DEFAULT '',
                text TEXT NOT NULL,
                send_at INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at INTEGER NOT NULL
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sched_due ON scheduled_messages(status, send_at)"
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS impersonation_backups(
                owner_id INTEGER PRIMARY KEY,
                connection_id TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                bio TEXT DEFAULT '',
                photo_file_id TEXT DEFAULT '',
                clock_was_enabled INTEGER DEFAULT 0,
                live_bio_was_enabled INTEGER DEFAULT 0,
                active INTEGER DEFAULT 0,
                target_id INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT ''
            )
        """)
        await conn.commit()
    finally:
        await conn.close()


# ─────────────────────── أرقام الإيموجي المميز (حسب أماكنها) ───────────────────────
BACK_ICON = "5445365692004071819"
BULB = custom_emoji("💡", "5767288287001580715")
SCHED_EMOJI = custom_emoji("🗓", "5967412305338568701")
SCHED_DONE = custom_emoji("✅", "5987929428536075624")
E_USER = custom_emoji("👤", "5904630315946611415")
E_USERNAME = custom_emoji("🔗", "5771887475421090729")
E_ID = custom_emoji("🆔", "5936017305585586269")
E_LANG = custom_emoji("🌐", "5776233299424843260")
E_SENT = custom_emoji("📨", "5890883384057533697")
E_TRANS = custom_emoji("🔁", "5890883384057533697")
E_WARN = custom_emoji("⚠️", "5278242578871894760")
E_RISK = custom_emoji("🛡", "5775887550262546277")
E_REASONS = custom_emoji("📋", "5989800655592627058")
HELP_SECTION_ICONS = {"manage": "5904258298764334001", "hidden": "5994473545650934240", "services": "5963312935148195483"}
HELP_ICONS = {
    "link": "5877465816030515018", "pin": "5796440171364749940", "cash": "5917828844936502300",
    "xo": "5193035611744804264", "links": "5766902139376898645", "translate": "5776233299424843260",
    "calc": "5935938364086685805", "scheduled": "5967412305338568701",
    "toggle": "5258476306152038031",
    "replies": "5258093637450866522",
    "muted": "5258318620722733379",
    "force": "5260268501515377807",
    "words": "5260342697075416641",
    "welcome": "5985478698722136468",
    "broadcast": "5445180664812968189",
    "tracking": "5904219717073114606",
    "payments": "5258204546391351475",
    "currency": "5902206159095339799",
    "social": "5447602197439218445",
    "media": "5445059250382469069",
    "clock": "5850317551090800862",
    "song": "5935955299142735525",
    "impersonate": "5985478698722136468",
}


# ───────────────────────────── مركز الشرح ─────────────────────────────

HELP_SECTIONS = {
    "manage": {
        "title": "إدارة وتحكم البوت",
        "layout": [["toggle", "link"], ["pin", "replies"], ["scheduled", "muted"], ["force", "words"], ["welcome", "broadcast"]],
        "items": [
            ("toggle", "التفعيل والتعطيل",
             "تشغيل أو إيقاف البوت على حسابك بالكامل. عند الإيقاف لا يرد البوت على أي عميل ولا ينفذ أي ميزة حتى تعيد تفعيله."),
            ("link", "شرح الربط",
             "لربط حسابك: افتح إعدادات تيليجرام ثم Telegram Business ثم Chatbots، واكتب يوزر البوت، وفعّل الصلاحيات التي يحتاجها (الرد على الرسائل وغيرها).\n\n"
             "بعد الربط يصلك إشعار بنجاح الربط، وتفتح لوحة التحكم بأمر /start."),
            ("pin", "تثبيت الرسائل",
             "ردّ على أي رسالة (منك أو من العميل) بكلمة تثبيت، فتُثبَّت الرسالة التي رددت عليها وتُحذف كلمة تثبيت تلقائيًا.\n\n"
             "مثال: ردّ على رسالة العميل التي فيها رقم المحفظة بكلمة تثبيت لتبقى مثبتة أعلى المحادثة."),
            ("replies", "الردود التلقائية",
             "أضف كلمة مفتاحية ورد جاهز، وعندما يكتبها العميل يرسل البوت الرد فورًا، مع إمكانية إضافة أزرار للرد."),
            ("scheduled", "الرسائل المجدولة",
             "من زر الرسائل المجدولة اختر عميلًا واكتب الرسالة ثم حدد الوقت، وسيرسلها البوت باسمك في الموعد.\n\n"
             "أمثلة للوقت: بعد 30 دقيقة — بعد 2 ساعة — 18:30 — 2026-11-05 09:00"),
            ("muted", "الكتم والسماح",
             "اكتم عميلًا معينًا فتُحذف رسائله تلقائيًا من المحادثة، ويمكنك السماح له من جديد بفك الكتم في أي وقت."),
            ("force", "الاشتراك الإجباري",
             "اشترط على عملائك الاشتراك في قنواتك قبل متابعة المحادثة، ويظهر لهم زر الاشتراك والتحقق."),
            ("words", "الكلمات الممنوعة",
             "حدد كلمات لا تريد ظهورها في محادثاتك، ويتعامل معها البوت تلقائيًا عند كتابتها."),
            ("welcome", "رسالة الترحيب",
             "اكتب رسالة ترحيب تُرسل للعميل تلقائيًا عند بدء المحادثة، ويمكنك إضافة ملصق أو صورة معها."),
            ("broadcast", "الإذاعة للعملاء",
             "أرسل رسالة واحدة لجميع عملائك دفعة واحدة."),
        ],
    },
    "hidden": {
        "title": "المميزات الخفية والأمان",
        "layout": [["translate", "tracking"], ["xo", "calc"], ["links", "song"], ["impersonate"]],
        "items": [
            ("translate", "الترجمة الفورية",
             "يكتشف البوت الرسائل غير العربية ويرسل ترجمتها إلى خاصك تلقائيًا.\n\n"
             "مثال: يرسل العميل رسالة إنجليزية، فتصلك بطاقة فيها بيانات العميل والرسالة الأصلية وترجمتها العربية، مع زر لفتح ملفه.\n\n"
             "ولترجمة رسالتك للعميل: اكتب رسالتك بالعربي وفي آخرها .en، فيمسح البوت رسالتك ويرسل ترجمتها الإنجليزية باسمك."),
            ("tracking", "تنبيهات التعديل والحذف",
             "عندما يعدّل العميل رسالة أو يحذفها يرسل لك البوت تنبيهًا بالنص الأصلي، ويمكنك تفعيل أو تعطيل كل نوع من قائمة رصد الحذف والتعديل."),
            ("xo", "لعبة XO",
             "اكتب xo (بحروف صغيرة وملتصقة) داخل المحادثة فتُمسح الرسالة ويظهر لوح اللعب ويلعب الطرفان بالدور.\n\n"
             "من كتب xo يلعب بعلامة X ويبدأ، والطرف الآخر بعلامة O. وبعد التعادل، من يضغط «جولة أخرى» هو الذي يبدأ الجولة الجديدة."),
            ("links", "كاشف الروابط المشبوهة",
             "عندما يرسل العميل رابطًا مشبوهًا يصلك تنبيه في خاصك فيه الرابط وسبب الشك ودرجة الخطورة، مع زر لفتح ملف العميل.\n\n"
             "يفحص البوت شكل الرابط فقط (مثل الروابط المختصرة وانتحال أسماء المواقع المشهورة)، ولا يفتح الرابط ولا يحذف أي رسالة."),
            ("song", "تنزيل الأغاني",
             "اكتب يوت ثم اسم الأغنية أو رابطها داخل المحادثة.\n\n"
             "مثال: يوت ويجز الحظ\n\n"
             "تُمسح رسالتك وتظهر رسالة جار البحث، وبعد التحميل تظهر الأغنية بغلافها واسمها والفنان والمدة. "
             "وإذا لم يجد الأغنية يرسل تعذر تنفيذ التحميل. أقصى مدة للعملية دقيقة."),
            ("calc", "الآلة الحاسبة",
             "فعّلها من الإعدادات المتقدمة ثم اكتب عملية حسابية في المحادثة وسيرد البوت بالناتج.\n\n"
             "أمثلة: 25*4 أو 100/2.\n\n"
             "ومن زر «معاينة الآلة الحاسبة» تجرّب آلة حاسبة بأزرار داخل البوت.\n\n"
             "وفي محادثة العميل اكتب calculator أو آلة فتظهر الآلة بأزرارها ليستخدمها الطرفان."),
            ("impersonate", "الانتحال",
             "اكتب كلمة انتحال أو انتحل داخل محادثة العميل فيمسح البوت رسالتك وينتحل حساب الطرف الآخر بالكامل (الاسم الأول والأخير، البايو، والصورة الشخصية) مع حفظ بياناتك الأصلية تلقائيًا.\n\n"
             "ولإلغاء الانتحال واسترجاع حسابك الأصلي: اكتب الغاء الانتحال أو مسح الانتحال أو الغاء انتحال في الشات، فيحذف البوت صورة المنتحل ويرجع صورتك الأساسية واسمك والبايو كما كانوا قبل الانتحال."),
        ],
    },
    "services": {
        "title": "الخدمات والماليات",
        "layout": [["cash", "currency"], ["payments"], ["social", "media"], ["clock"]],
        "items": [
            ("cash", "خدمات الكاش",
             "افتح طرق الدفع واختر «شبكات مصرية» ثم الخدمة (فودافون كاش أو أورنج كاش أو وي كاش أو اتصالات كاش)، ثم اضغط تعديل البيانات واكتب رقم المحفظة الذي تستقبل عليه. بعدها فعّل الطريقة.\n\n"
             "طريقة طلب العميل: يكتب العميل اسم الطريقة، مثل فودافون كاش، فيظهر له الرقم مع زر نسخ.\n\n"
             "المبلغ: إذا كان التحويل لرقم مصري، يرسل العميل الرقم ثم المبلغ في رسالة واحدة، مثل: 01012345678 250 فيعرض البوت أكواد التحويل المناسبة للمبلغ. أما رقم المحفظة نفسه فيُرسل من زر طريقة الدفع، وليس مع المبلغ.\n\n"
             "مثال الإعداد: رقم فودافون كاش 01012345678 — والمبلغ المطلوب: 250 جنيهًا."),
            ("currency", "محول العملات",
             "اكتب مبلغًا مع العملة، وسيعرض البوت قيمته بالعملات الأخرى حسب السعر الحالي.\n\n"
             "مثال: TON 50 أو USD 100."),
            ("payments", "طرق الدفع",
             "من طرق الدفع فعّل الوسيلة المطلوبة، ثم اضغط تعديل البيانات لإضافة الرقم أو العنوان.\n\n"
             "مثال: فعّل Binance وأضف معرّف الحساب لاستلام التحويلات."),
            ("social", "إدارة السوشيال ميديا",
             "أضف روابط حساباتك على مواقع التواصل ليعرضها البوت للعملاء."),
            ("media", "إدارة الميديا",
             "تحكم في أنواع الوسائط التي يتعامل معها البوت في محادثاتك."),
            ("clock", "الساعة الحية",
             "تضيف الوقت الحالي إلى اسم حسابك وتحدّثه تلقائيًا كل دقيقة، مع عدة أشكال للأرقام."),
        ],
    },
}

HELP_INDEX = {
    key: (sec, title, text)
    for sec, data in HELP_SECTIONS.items()
    for key, title, text in data["items"]
}


def help_home_kb():
    rows = [
        [InlineKeyboardButton(text=data["title"], callback_data=f"help_s:{sec}", style="primary",
                              icon_custom_emoji_id=HELP_SECTION_ICONS.get(sec))]
        for sec, data in HELP_SECTIONS.items()
    ]
    rows.append([InlineKeyboardButton(text="رجوع", callback_data="home", style="danger", icon_custom_emoji_id=BACK_ICON)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def help_section_kb(sec):
    titles = {key: title for key, title, _ in HELP_SECTIONS[sec]["items"]}
    rows = [
        [InlineKeyboardButton(text=titles[key], callback_data=f"help_f:{key}", style="primary",
                              icon_custom_emoji_id=HELP_ICONS.get(key)) for key in row]
        for row in HELP_SECTIONS[sec]["layout"]
    ]
    rows.append([InlineKeyboardButton(text="رجوع للأقسام", callback_data="help_home", style="danger", icon_custom_emoji_id=BACK_ICON)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "help_home")
async def help_home(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await edit_or_replace(
        call,
        f"<b>{BULB} مركز الشرح</b>\n\n<blockquote>اختر القسم الذي تريد معرفة طريقة استخدامه مع مثال عملي.</blockquote>",
        help_home_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("help_s:"))
async def help_section(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    sec = call.data.split(":", 1)[1]
    if sec not in HELP_SECTIONS:
        await call.answer()
        return
    await edit_or_replace(
        call,
        f"<b>{BULB} {HELP_SECTIONS[sec]['title']}</b>\n\n<blockquote>اختر الميزة لعرض شرحها وطريقة استخدامها:</blockquote>",
        help_section_kb(sec),
    )
    await call.answer()


@router.callback_query(F.data.startswith("help_f:"))
async def help_feature(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    key = call.data.split(":", 1)[1]
    entry = HELP_INDEX.get(key)
    if not entry:
        await call.answer()
        return
    sec, title, text = entry
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="رجوع للميزات", callback_data=f"help_s:{sec}", style="danger", icon_custom_emoji_id=BACK_ICON)]
    ])
    await edit_or_replace(
        call,
        f"<b>{BULB} {safe_html(title)}</b>\n\n<blockquote>{safe_html(text)}</blockquote>",
        kb,
    )
    await call.answer()


# ─────────────────────────── الإعدادات المتقدمة ───────────────────────────

@router.callback_query(F.data == "advanced")
async def advanced_settings(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await state.clear()
    await edit_or_replace(call, advanced_text(), advanced_kb())
    await call.answer()


# ─────────────────────── الترجمة الفورية وكارت العميل ───────────────────────

_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)

LANGUAGE_NAMES_AR = {
    "en": "الإنجليزية", "fr": "الفرنسية", "de": "الألمانية", "es": "الإسبانية",
    "it": "الإيطالية", "pt": "البرتغالية", "tr": "التركية", "ru": "الروسية",
    "fa": "الفارسية", "ur": "الأوردية", "hi": "الهندية", "id": "الإندونيسية",
    "ms": "الماليزية", "bn": "البنغالية", "nl": "الهولندية", "pl": "البولندية",
    "uk": "الأوكرانية", "sv": "السويدية", "el": "اليونانية", "he": "العبرية",
    "iw": "العبرية", "ja": "اليابانية", "ko": "الكورية", "zh-CN": "الصينية",
    "zh-TW": "الصينية", "zh": "الصينية", "th": "التايلاندية", "vi": "الفيتنامية",
    "ku": "الكردية", "so": "الصومالية", "sw": "السواحلية", "am": "الأمهرية",
}


def needs_translation(text):
    t = (text or "").strip()
    if not t or t.startswith("/"):
        return False
    letters = _LETTER_RE.findall(t)
    if not letters:
        return False
    arabic = sum(1 for ch in letters if _ARABIC_CHAR_RE.match(ch))
    return (arabic / len(letters)) < 0.3


_TRANSLATE_HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"}


def parse_gtx_response(data):
    """الصيغة: [[["ترجمة","أصل",...],...], null, "en", ...]"""
    parts = data[0] or []
    translated = "".join(p[0] for p in parts if p and p[0])
    lang = data[2] if len(data) > 2 and isinstance(data[2], str) else ""
    return translated.strip(), lang


def parse_clients5_response(data):
    """الصيغتان المحتملتان: {"sentences":[{"trans":..}],"src":"en"} أو [["ترجمة","en"]]"""
    if isinstance(data, dict):
        sentences = data.get("sentences") or []
        return "".join(x.get("trans", "") for x in sentences).strip(), str(data.get("src", ""))
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, list):
            return str(first[0]).strip(), (str(first[1]) if len(first) > 1 else "")
        return str(first).strip(), ""
    return "", ""


async def google_translate(text, target="ar"):
    """يجرّب مصدرين للترجمة ويسجّل سبب أي فشل بوضوح."""
    text = text[:1800]
    sources = [
        ("gtx", "https://translate.googleapis.com/translate_a/single",
         {"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text}, parse_gtx_response),
        ("clients5", "https://clients5.google.com/translate_a/t",
         {"client": "dict-chrome-ex", "sl": "auto", "tl": target, "q": text}, parse_clients5_response),
    ]
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout, headers=_TRANSLATE_HEADERS) as session:
        for name, url, params, parser in sources:
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        logger.warning("Translation source %s returned HTTP %s", name, resp.status)
                        continue
                    data = await resp.json(content_type=None)
                translated, lang = parser(data)
                if translated:
                    return translated, lang
                logger.warning("Translation source %s returned an empty result", name)
            except Exception as exc:
                logger.warning("Translation source %s failed: %r", name, exc)
    return None, ""


async def google_translate_to_ar(text):
    return await google_translate(text, "ar")


async def send_translation_card(bot, owner_id, message):
    try:
        text_raw = message.text or message.caption or ""
        if not needs_translation(text_raw):
            return
        translated, lang = await google_translate_to_ar(text_raw)
        if not translated:
            logger.warning("Translation card skipped: all translation sources failed")
            return
        if lang.lower().startswith("ar"):
            return
        if translated.strip().lower() == text_raw.strip().lower():
            return
        sender = message.from_user or message.chat
        name = getattr(sender, "full_name", None) or getattr(sender, "first_name", None) or "—"
        username = getattr(sender, "username", None)
        sender_id = sender.id
        lang_label = LANGUAGE_NAMES_AR.get(lang, lang.upper() if lang else "غير معروفة")
        username_text = f"@{safe_html(username)}" if username else "غير معروف"
        card = (
            f"{E_USER} <b>Sender:</b> {safe_html(name)}\n"
            f"{E_USERNAME} <b>Username:</b> {username_text}\n"
            f"{E_ID} <b>User ID:</b> <code>{sender_id}</code>\n"
            f"{E_LANG} <b>Language:</b> {safe_html(lang_label)}\n\n"
            f"{E_SENT} <b>The message sent :</b>\n<blockquote>{safe_html(text_raw[:1500])}</blockquote>\n"
            f"{E_TRANS} <b>Translation of the message :</b>\n<blockquote>{safe_html(translated)}</blockquote>"
        )
        url = f"https://t.me/{username}" if username else f"tg://user?id={sender_id}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Open Customer Profile", url=url, style="primary")]
        ])
        await bot.send_message(owner_id, card, parse_mode="HTML", reply_markup=kb)
        logger.info("Translation card sent to %s for a %s message", owner_id, lang or "unknown")
    except Exception:
        logger.warning("Failed to send translation card", exc_info=True)


async def recover_business_connection(bot, bc_id):
    """إذا وصلت رسالة من اتصال غير مسجّل (مثلًا بعد تغيير قاعدة البيانات)،
    نجلب بيانات الاتصال من تيليجرام ونسجّله بدل تجاهل الرسالة."""
    try:
        info = await bot.get_business_connection(business_connection_id=bc_id)
    except Exception as exc:
        logger.warning("Could not recover business connection %s: %r", bc_id, exc)
        return None
    rights = getattr(info, "rights", None)
    can_reply = int(bool(getattr(rights, "can_reply", False)))
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO business(connection_id, user_id, enabled, can_reply, original_name, original_last_name, can_edit_name, can_edit_bio) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(connection_id) DO UPDATE SET "
            "user_id=excluded.user_id, enabled=excluded.enabled, can_reply=excluded.can_reply",
            (info.id, info.user.id, int(info.is_enabled), can_reply,
             info.user.first_name or "", info.user.last_name or "",
             int(bool(getattr(rights, "can_edit_name", False))),
             int(bool(getattr(rights, "can_edit_bio", False)))),
        )
        await conn.commit()
    finally:
        await conn.close()
    await ensure_account_settings(info.user.id)
    if info.is_enabled:
        await set_account_setting(info.user.id, "enabled", 1)
    logger.info("Recovered business connection %s for user %s", bc_id, info.user.id)
    return {"user_id": info.user.id, "enabled": int(info.is_enabled), "can_reply": can_reply}


# ───────────────────────────────── لعبة XO ─────────────────────────────────

XO_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
XO_GAMES = {}
XO_MAX_GAMES = 300


def xo_winner(board):
    for a, b, c in XO_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


XO_BLANK = "\u2800"  # نص فارغ لأزرار اللوحة (الألوان هي التي تحدد اللاعب)
# أرقام الإيموجي المميز: ضع الرقم بدل None لاحقًا، وإن بقي None يظهر الإيموجي العادي.
XO_EMOJI = {
    "title": ("5938413566624272793", "🎮"),
    "X": ("5409106676148099677", "❌"),
    "O": ("5409266517650987224", "⭕"),
    "turn": ("5906995262378741881", "🎙"),
    "party": ("6206378324273403309", "🎉"),
}


def xo_emoji(key):
    emoji_id, fallback = XO_EMOJI[key]
    return f"<tg-emoji emoji-id='{emoji_id}'>{fallback}</tg-emoji>" if emoji_id else fallback


def xo_kb(gid, game):
    """اللوحة بالألوان: الخانة الفارغة رمادية، X أخضر، O أحمر."""
    style_of = {"X": "success", "O": "danger"}
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            row.append(InlineKeyboardButton(
                text=XO_BLANK, callback_data=f"xo:{gid}:{i}",
                style=style_of.get(game["board"][i]),
            ))
        rows.append(row)
    if game["over"]:
        if not game["winner"]:  # تعادل فقط: زر جولة أخرى، وبعد الفوز لا توجد أزرار
            rows.append([InlineKeyboardButton(text="جولة أخرى", callback_data=f"xo_new:{gid}", style="success")])
    elif not any(game["board"]):
        rows.append([InlineKeyboardButton(text="Close", callback_data=f"xo_close:{gid}", style="danger", icon_custom_emoji_id="5879895758202735862")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def xo_text(game):
    names = game["names"]
    if game["over"]:
        if game["winner"]:
            winner = game["winner"]
            return (
                f"<b>{xo_emoji('party')} انتهت اللعبة! الفائز هو:</b>\n\n"
                f"<b>{safe_html(names[winner])}</b> {xo_emoji(winner)}"
            )
        return f"<b>{xo_emoji('party')} انتهت اللعبة! لا يوجد فائز</b>"
    head = f"<b>{xo_emoji('title')} لعبة X - O</b>\n\n"
    players = (
        f"{xo_emoji('X')} : <b>{safe_html(names['X'])}</b>\n"
        f"{xo_emoji('O')} : <b>{safe_html(names['O'])}</b>\n\n"
    )
    status = f"{xo_emoji('turn')} الآن دور : <b>{safe_html(names[game['turn']])}</b>"
    return head + players + status


async def maybe_start_xo(message, owner_id, bc_id, is_owner_message=True):
    if (message.text or "").strip() != "xo":
        return False
    owner_name = "المالك"
    try:
        owner_chat = await message.bot.get_chat(owner_id)
        owner_name = getattr(owner_chat, "full_name", None) or owner_name
    except Exception:
        pass
    customer_id = message.chat.id
    customer_name = getattr(message.chat, "full_name", None) or message.chat.first_name or "العميل"
    # اللي كتب xo هو X وهو اللي يبدأ
    if is_owner_message:
        x_id, x_name, o_id, o_name = owner_id, owner_name, customer_id, customer_name
    else:
        x_id, x_name, o_id, o_name = customer_id, customer_name, owner_id, owner_name
    gid = secrets.token_hex(3)
    game = {
        "board": [""] * 9, "turn": "X", "over": False, "winner": None,
        "players": {"X": x_id, "O": o_id},
        "names": {"X": x_name, "O": o_name},
        "bc_id": bc_id, "chat_id": message.chat.id,
    }
    while len(XO_GAMES) >= XO_MAX_GAMES:
        XO_GAMES.pop(next(iter(XO_GAMES)))
    XO_GAMES[gid] = game
    try:
        await message.bot.send_message(
            chat_id=message.chat.id, text=xo_text(game), reply_markup=xo_kb(gid, game),
            parse_mode="HTML", business_connection_id=bc_id,
        )
    except Exception:
        XO_GAMES.pop(gid, None)
        logger.warning("Failed to start XO game", exc_info=True)
        return False
    await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
    return True

async def xo_refresh(call, gid, game):
    try:
        await call.message.edit_text(xo_text(game), reply_markup=xo_kb(gid, game), parse_mode="HTML")
    except Exception:
        logger.warning("XO refresh failed", exc_info=True)


@router.callback_query(F.data.startswith("xo:"))
async def xo_move(call: CallbackQuery):
    try:
        _, gid, cell = call.data.split(":")
        i = int(cell)
    except ValueError:
        await call.answer()
        return
    game = XO_GAMES.get(gid)
    if not game:
        await call.answer("انتهت هذه اللعبة.", show_alert=True)
        return
    uid = call.from_user.id
    players = game["players"]
    if uid not in (players["X"], players["O"]):
        await call.answer("هذه اللعبة ليست لك.", show_alert=True)
        return
    if game["over"]:
        await call.answer()
        return
    turn = game["turn"]
    if players["X"] != players["O"] and players[turn] != uid:
        await call.answer("ليس دورك الآن.")
        return
    if not 0 <= i <= 8 or game["board"][i]:
        await call.answer("هذه الخانة مستخدمة.")
        return
    game["board"][i] = turn
    winner = xo_winner(game["board"])
    if winner:
        game["winner"], game["over"] = winner, True
    elif all(game["board"]):
        game["over"] = True
    else:
        game["turn"] = "O" if turn == "X" else "X"
    await xo_refresh(call, gid, game)
    await call.answer()


@router.callback_query(F.data.startswith("xo_new:"))
async def xo_new(call: CallbackQuery):
    gid = call.data.split(":", 1)[1]
    game = XO_GAMES.get(gid)
    if not game:
        await call.answer("انتهت هذه اللعبة.", show_alert=True)
        return
    if call.from_user.id not in game["players"].values():
        await call.answer("هذه اللعبة ليست لك.", show_alert=True)
        return
    if not game["over"] or game["winner"]:
        await call.answer()
        return
    players, names = game["players"], game["names"]
    # اللي يضغط «جولة أخرى» هو اللي يصبح X ويبدأ
    if players["X"] != players["O"] and call.from_user.id == players["O"]:
        players["X"], players["O"] = players["O"], players["X"]
        names["X"], names["O"] = names["O"], names["X"]
    game.update({"board": [""] * 9, "turn": "X", "over": False, "winner": None})
    await xo_refresh(call, gid, game)
    await call.answer()

@router.callback_query(F.data.startswith("xo_close:"))
async def xo_close(call: CallbackQuery):
    gid = call.data.split(":", 1)[1]
    game = XO_GAMES.get(gid)
    if game and call.from_user.id not in game["players"].values():
        await call.answer("هذه اللعبة ليست لك.", show_alert=True)
        return
    XO_GAMES.pop(gid, None)
    bc_id = getattr(call.message, "business_connection_id", None) or (game or {}).get("bc_id")
    deleted = False
    if bc_id:
        try:
            await call.bot.delete_business_messages(
                business_connection_id=bc_id, message_ids=[call.message.message_id]
            )
            deleted = True
        except Exception:
            logger.debug("XO close: delete failed", exc_info=True)
    if not deleted:
        try:
            await call.message.edit_text("<b>🎮 تم إغلاق اللعبة.</b>", parse_mode="HTML")
        except Exception:
            pass
    await call.answer()


# ───────────────────────────── الرسائل المجدولة ─────────────────────────────

class ScheduleSG(StatesGroup):
    text = State()
    when = State()


_DIGITS_AR = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_REL_RE = re.compile(r"^(?:بعد\s*)?(?:(\d{1,4})\s*)?([^\d\s]+)$", re.IGNORECASE)
_DUAL_UNITS = {
    "دقيقتين": ("minutes", 2), "دقيقتان": ("minutes", 2),
    "ساعتين": ("hours", 2), "ساعتان": ("hours", 2),
    "يومين": ("days", 2), "يومان": ("days", 2),
}
_UNITS = {
    "minutes": {"د", "دقيقة", "دقيقه", "دقايق", "دقائق", "m", "min", "mins", "minute", "minutes"},
    "hours": {"س", "ساعة", "ساعه", "ساعات", "h", "hr", "hrs", "hour", "hours"},
    "days": {"ي", "يوم", "ايام", "أيام", "d", "day", "days"},
}


def parse_when(value, tz=None, now=None):
    """يحوّل نص الوقت إلى datetime مع منطقة زمنية، أو None إذا كانت الصيغة غير مفهومة."""
    tz = tz or BOT_TZ
    now = now or datetime.now(tz)
    t = (value or "").strip().translate(_DIGITS_AR)
    if not t:
        return None
    result = None
    m = _REL_RE.match(t)
    if m and (m.group(1) or t.startswith("بعد")):
        amount_txt, unit = m.group(1), m.group(2).lower()
        name, amount = None, 0
        if not amount_txt and unit in _DUAL_UNITS:
            name, amount = _DUAL_UNITS[unit]
        else:
            amount = int(amount_txt) if amount_txt else 1
            name = next((n for n, words in _UNITS.items() if unit in words), None)
        if name and amount > 0:
            result = now + timedelta(**{name: amount})
    if result is None:
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            if hour > 23 or minute > 59:
                return None
            result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if result <= now:
                result += timedelta(days=1)
    if result is None:
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", t)
        if m:
            try:
                result = datetime(*(int(x) for x in m.groups()), tzinfo=tz)
            except ValueError:
                return None
    if result is None:
        return None
    if result < now + timedelta(seconds=30) or result > now + timedelta(days=365):
        return None
    return result


def sched_home_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إضافة رسالة مجدولة", callback_data="sched_add", style="success", icon_custom_emoji_id="6206375377925839184")],
        [InlineKeyboardButton(text="الرسائل المنتظرة", callback_data="sched_list", style="primary", icon_custom_emoji_id="5967382867632722656")],
        [InlineKeyboardButton(text="رجوع", callback_data="home", style="danger")],
    ])


async def _sched_connection(user_id):
    conn = await db()
    try:
        return await fetchone(
            conn, "SELECT connection_id FROM business WHERE user_id=? AND enabled=1 LIMIT 1", (user_id,)
        )
    finally:
        await conn.close()


@router.callback_query(F.data == "scheduled")
async def sched_home(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await state.clear()
    conn = await db()
    try:
        row = await fetchone(
            conn,
            "SELECT COUNT(*) c FROM scheduled_messages WHERE owner_id=? AND status='pending'",
            (call.from_user.id,),
        )
    finally:
        await conn.close()
    pending = row["c"] if row else 0
    await edit_or_replace(
        call,
        f"<b>{SCHED_EMOJI} الرسائل المجدولة</b>\n\n<blockquote>أرسل رسالة لأي عميل في وقت تحدده، وسيرسلها البوت باسمك تلقائيًا."
        f"\n\nالرسائل المنتظرة حاليًا: <b>{pending}</b></blockquote>",
        sched_home_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "sched_add")
async def sched_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    biz = await _sched_connection(call.from_user.id)
    if not biz:
        await call.answer("اربط حسابك بالبوت أولاً.", show_alert=True)
        return
    conn = await db()
    try:
        rows = await conn.execute_fetchall(
            "SELECT chat_id, first_name, username FROM customers WHERE connection_id=? "
            "ORDER BY last_seen DESC LIMIT 12",
            (biz["connection_id"],),
        )
    finally:
        await conn.close()
    if not rows:
        await edit_or_replace(
            call,
            f"<b>{SCHED_EMOJI} الرسائل المجدولة</b>\n\n<blockquote>لا يوجد عملاء بعد. سيظهر العميل هنا بعد أن يراسلك.</blockquote>",
            back_kb("scheduled"),
        )
        await call.answer()
        return
    buttons = []
    for r in rows:
        label = r["first_name"] or (f"@{r['username']}" if r["username"] else str(r["chat_id"]))
        buttons.append([InlineKeyboardButton(text=label[:40], callback_data=f"sched_c:{r['chat_id']}", style="primary")])
    buttons.append([InlineKeyboardButton(text="رجوع", callback_data="scheduled", style="danger")])
    await edit_or_replace(
        call,
        f"<b>{SCHED_EMOJI} الرسائل المجدولة</b>\n\n<blockquote>اختر العميل الذي تريد إرسال الرسالة له:</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await call.answer()


@router.callback_query(F.data.startswith("sched_c:"))
async def sched_pick(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    try:
        chat_id = int(call.data.split(":", 1)[1])
    except ValueError:
        await call.answer()
        return
    biz = await _sched_connection(call.from_user.id)
    if not biz:
        await call.answer("اربط حسابك بالبوت أولاً.", show_alert=True)
        return
    conn = await db()
    try:
        cust = await fetchone(
            conn,
            "SELECT first_name, username FROM customers WHERE connection_id=? AND chat_id=?",
            (biz["connection_id"], chat_id),
        )
    finally:
        await conn.close()
    if not cust:
        await call.answer("العميل غير موجود.", show_alert=True)
        return
    name = cust["first_name"] or (f"@{cust['username']}" if cust["username"] else str(chat_id))
    await state.clear()
    await state.update_data(sched_chat_id=chat_id, sched_name=name, sched_conn=biz["connection_id"])
    await state.set_state(ScheduleSG.text)
    await edit_or_replace(
        call,
        f"<b>{SCHED_EMOJI} الرسالة إلى: {safe_html(name)}</b>\n\n<blockquote>اكتب الآن نص الرسالة التي تريد إرسالها.</blockquote>",
        back_kb("scheduled"),
    )
    await call.answer()


@router.message(ScheduleSG.text)
async def sched_text(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("أرسل نص الرسالة كتابةً.")
        return
    if len(message.text) > 4000:
        await message.answer("الرسالة طويلة جدًا، اختصرها وأرسلها مرة أخرى.")
        return
    await state.update_data(sched_text=message.html_text)
    await state.set_state(ScheduleSG.when)
    await message.answer(
        f"<b>{SCHED_EMOJI} متى تريد إرسال الرسالة؟</b>\n\n<blockquote>اكتب الوقت بإحدى الصيغ:\n"
        "• بعد 30 دقيقة\n• بعد 2 ساعة\n• بعد يوم\n• 18:30 (اليوم أو غدًا إذا مضى الوقت)\n"
        "• 2026-11-05 09:00</blockquote>",
        parse_mode="HTML",
        reply_markup=back_kb("scheduled"),
    )


@router.message(ScheduleSG.when)
async def sched_when(message: Message, state: FSMContext):
    when = parse_when(message.text or "")
    if not when:
        await message.answer(
            "<blockquote>صيغة الوقت غير مفهومة أو أن الوقت مضى. جرّب مثل: <b>بعد 30 دقيقة</b> أو <b>18:30</b>.</blockquote>",
            parse_mode="HTML",
        )
        return
    data = await state.get_data()
    chat_id = data.get("sched_chat_id")
    text = data.get("sched_text")
    connection_id = data.get("sched_conn")
    if not (chat_id and text and connection_id):
        await state.clear()
        await message.answer("انتهت الجلسة، ابدأ من جديد.", reply_markup=sched_home_kb())
        return
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO scheduled_messages(owner_id, connection_id, chat_id, customer_name, text, send_at, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (
                message.from_user.id, connection_id, chat_id, data.get("sched_name", ""), text,
                int(when.timestamp()), int(datetime.now(timezone.utc).timestamp()),
            ),
        )
        await conn.commit()
    finally:
        await conn.close()
    await state.clear()
    await message.answer(
        f"<blockquote>{SCHED_DONE} <b>تمت الجدولة</b>\n\nإلى: {safe_html(data.get('sched_name', ''))}\n"
        f"الموعد: <b>{when.strftime('%Y-%m-%d %H:%M')}</b></blockquote>",
        parse_mode="HTML",
        reply_markup=sched_home_kb(),
    )


async def _render_sched_list(call: CallbackQuery):
    conn = await db()
    try:
        rows = await conn.execute_fetchall(
            "SELECT id, customer_name, text, send_at FROM scheduled_messages "
            "WHERE owner_id=? AND status='pending' ORDER BY send_at LIMIT 15",
            (call.from_user.id,),
        )
    finally:
        await conn.close()
    if not rows:
        await edit_or_replace(
            call,
            f"<b>{SCHED_EMOJI} الرسائل المجدولة</b>\n\n<blockquote>لا توجد رسائل منتظرة.</blockquote>",
            back_kb("scheduled"),
        )
        return
    lines, buttons = [], []
    for n, r in enumerate(rows, 1):
        when = datetime.fromtimestamp(r["send_at"], BOT_TZ).strftime("%m-%d %H:%M")
        preview = re.sub(r"<[^>]+>", "", r["text"])[:30]
        lines.append(f"{n}. {safe_html(r['customer_name'])} — {when}\n    {safe_html(preview)}")
        buttons.append([InlineKeyboardButton(text=f"حذف {n}", callback_data=f"sched_del:{r['id']}", style="danger", icon_custom_emoji_id="5879896690210639947")])
    buttons.append([InlineKeyboardButton(text="رجوع", callback_data="scheduled", style="primary")])
    await edit_or_replace(
        call,
        f"<b>{SCHED_EMOJI} الرسائل المنتظرة</b>\n\n<blockquote>" + "\n\n".join(lines) + "</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "sched_list")
async def sched_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _render_sched_list(call)
    await call.answer()


@router.callback_query(F.data.startswith("sched_del:"))
async def sched_delete(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    try:
        sid = int(call.data.split(":", 1)[1])
    except ValueError:
        await call.answer()
        return
    conn = await db()
    try:
        await conn.execute(
            "UPDATE scheduled_messages SET status='cancelled' WHERE id=? AND owner_id=? AND status='pending'",
            (sid, call.from_user.id),
        )
        await conn.commit()
    finally:
        await conn.close()
    await _render_sched_list(call)
    await call.answer("تم حذف الرسالة المجدولة.")


async def scheduled_worker(bot):
    while True:
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            conn = await db()
            try:
                rows = await conn.execute_fetchall(
                    "SELECT id, owner_id, connection_id, chat_id, customer_name, text FROM scheduled_messages "
                    "WHERE status='pending' AND send_at<=? ORDER BY send_at LIMIT 50",
                    (now,),
                )
                for r in rows:
                    status = "sent"
                    try:
                        if not await paid_access_allowed(r["owner_id"]):
                            raise RuntimeError("no active subscription")
                        await bot.send_message(
                            chat_id=r["chat_id"], text=r["text"], parse_mode="HTML",
                            business_connection_id=r["connection_id"],
                        )
                    except Exception:
                        logger.warning("Scheduled message %s failed", r["id"], exc_info=True)
                        status = "failed"
                    await conn.execute("UPDATE scheduled_messages SET status=? WHERE id=?", (status, r["id"]))
                    await conn.commit()
                    if status == "failed":
                        try:
                            await bot.send_message(
                                r["owner_id"],
                                f"⚠️ تعذر إرسال الرسالة المجدولة إلى {safe_html(r['customer_name'])}.",
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass
            finally:
                await conn.close()
        except Exception:
            logger.exception("Scheduled worker error")
        await asyncio.sleep(15)

# ───────────────────────── الآلة الحاسبة بالأزرار (معاينة) ─────────────────────────

import ast
import operator

CALC_MAX_LEN = 40
CALC_ICON_ID = "5935938364086685805"
_CALC_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_CALC_OPCHAR = {"add": "+", "sub": "-", "mul": "*", "div": "/"}
CALC_LAYOUT = [
    [("1", "1"), ("2", "2"), ("3", "3"), ("+", "add")],
    [("4", "4"), ("5", "5"), ("6", "6"), ("-", "sub")],
    [("7", "7"), ("8", "8"), ("9", "9"), ("×", "mul")],
    [("0", "0"), (".", "dot"), ("C", "clr"), ("÷", "div")],
    [("⌫", "bs"), ("=", "eq")],
]


def calc_eval(expr):
    """تقييم آمن لتعبير حسابي بسيط (أرقام و + - * / فقط)."""
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = ev(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("unsupported expression")
    return ev(ast.parse(expr, mode="eval"))


def calc_format(value):
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("not finite")
        if value.is_integer() and abs(value) < 1e15:
            value = int(value)
        else:
            text = f"{value:.10f}".rstrip("0").rstrip(".")
            return text if len(text) <= 30 else f"{value:.6g}"
    text = str(value)
    return text if len(text) <= 30 else f"{float(value):.6g}"


def calc_apply(state, key):
    """يعيد الحالة الجديدة، أو None إذا لم يتغير شيء.
    الحالة نص عادي مثل "12+3.5"، وتبدأ بـ = إذا كانت نتيجة، و "=E" عند الخطأ."""
    result_mode = state.startswith("=")
    cur = state[1:] if result_mode else state
    if key == "clr":
        return "" if state else None
    if key == "bs":
        new = "" if result_mode else cur[:-1]
        return new if new != state else None
    if len(key) == 1 and key.isdigit():
        if result_mode:
            new = key
        else:
            token = re.search(r"[0-9.]*$", cur).group(0)
            new = cur[:-1] + key if token == "0" else cur + key
    elif key == "dot":
        if result_mode:
            new = "0."
        else:
            token = re.search(r"[0-9.]*$", cur).group(0)
            if "." in token:
                return None
            new = cur + ("0." if token == "" else ".")
    elif key in _CALC_OPCHAR:
        op = _CALC_OPCHAR[key]
        if result_mode:
            if cur == "E":
                return None
            new = cur + op
        elif cur == "":
            new = "-" if op == "-" else "0" + op
        elif cur[-1] in "+-*/":
            if cur == "-":
                return None
            new = cur[:-1] + op
        else:
            new = cur + op
    elif key == "eq":
        if result_mode or not cur:
            return None
        expr = cur.rstrip("+-*/.")
        if not expr or not re.search(r"[0-9]", expr):
            return None
        try:
            return "=" + calc_format(calc_eval(expr))
        except Exception:
            return "=E"
    else:
        return None
    return new if len(new) <= CALC_MAX_LEN else None


def calc_display(state):
    if state == "=E":
        return "خطأ"
    cur = state[1:] if state.startswith("=") else state
    return cur.replace("*", "×").replace("/", "÷") or "0"


def calc_text(state):
    return (
        f"<blockquote><b><tg-emoji emoji-id='{CALC_ICON_ID}'>🧮</tg-emoji> الآلة الحاسبة</b>\n\n"
        f"{safe_html(calc_display(state))}</blockquote>\n"
        "اختر الأرقام والعمليات من اللوحة بالأسفل."
    )


def calc_kb(state):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"cp:{key}:{state}", style="primary") for label, key in row]
        for row in CALC_LAYOUT
    ])


@router.callback_query(F.data == "calc_preview")
async def calc_preview(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await call.message.answer(calc_text(""), reply_markup=calc_kb(""), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("cp:"))
async def calc_press(call: CallbackQuery):
    try:
        _, key, state = call.data.split(":", 2)
    except ValueError:
        await call.answer()
        return
    new_state = calc_apply(state, key)
    if new_state is None or new_state == state:
        await call.answer()
        return
    try:
        await call.message.edit_text(calc_text(new_state), reply_markup=calc_kb(new_state), parse_mode="HTML")
    except Exception:
        logger.debug("Calculator edit failed", exc_info=True)
    await call.answer()


# ─────────────── الآلة الحاسبة داخل شات العميل (بكلمة) ───────────────

def normalize_trigger(text):
    t = (text or "").strip().lower()
    t = t.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي"}))
    return re.sub(r"\s+", " ", t)


# بعد التطبيع: ة→ه وأ/إ/آ→ا، فتغطي: آلة / ألة / الة / اله / الآلة / الة حاسبة / اله حاسبه ...
CALC_TRIGGERS = {"calculator", "اله", "الاله", "اله حاسبه", "الاله حاسبه", "اله الحاسبه", "الاله الحاسبه"}


async def maybe_start_calculator(message, owner_id, bc_id):
    if normalize_trigger(message.text) not in CALC_TRIGGERS:
        return False
    if not await get_account_setting(owner_id, "calculator_enabled"):
        return False
    try:
        await message.bot.send_message(
            chat_id=message.chat.id, text=calc_text(""), reply_markup=calc_kb(""),
            parse_mode="HTML", business_connection_id=bc_id,
        )
    except Exception:
        logger.warning("Failed to send calculator", exc_info=True)
        return False
    await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
    return True


# ─────────────── ترجمة رسالتك للعميل بكلمة .en في آخرها ───────────────

try:
    from aiogram.types import MessageEntity, ReplyParameters
except Exception:  # للاختبارات خارج aiogram فقط
    MessageEntity = ReplyParameters = None

_EN_SUFFIX_RE = re.compile(r"^(.*\S)\s*\.en\s*$", re.S | re.I)


def utf16_len(text):
    return len(text.encode("utf-16-le")) // 2


async def maybe_translate_outgoing(message, bc_id):
    """رسالتك المنتهية بـ .en: نمسحها ونرسل ترجمتها الإنجليزية باسمك."""
    match = _EN_SUFFIX_RE.match(message.text or "")
    if not match:
        return False
    body = match.group(1).strip()
    if not body:
        return False
    translated, _lang = await google_translate(body, "en")
    if not translated:
        logger.warning("Outgoing translation skipped: all translation sources failed")
        return False
    kwargs = {
        "chat_id": message.chat.id,
        # حرف غير مرئي بتنسيق خاص: وجود entities يمنع تغليف الرسالة بالاقتباس، فتصل للعميل كرسالة عادية
        "text": translated + "\u200b",
        "entities": [MessageEntity(type="bold", offset=utf16_len(translated), length=1)],
        "parse_mode": None,
        "business_connection_id": bc_id,
    }
    if message.reply_to_message and ReplyParameters is not None:
        kwargs["reply_parameters"] = ReplyParameters(message_id=message.reply_to_message.message_id)
    try:
        await message.bot.send_message(**kwargs)
    except Exception:
        logger.warning("Failed to send outgoing translation", exc_info=True)
        return False
    await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
    return True


# ─────────────────────────── كاشف الروابط المشبوهة ───────────────────────────

from urllib.parse import urlsplit

LINK_WHITELIST = (
    "t.me", "telegram.org", "telegram.me", "telegra.ph", "youtube.com", "youtu.be", "google.com",
    "instagram.com", "facebook.com", "fb.com", "x.com", "twitter.com", "tiktok.com", "wikipedia.org",
    "whatsapp.com", "wa.me", "github.com", "apple.com", "microsoft.com", "amazon.com", "linkedin.com",
    "snapchat.com", "binance.com", "bybit.com", "ton.org", "fragment.com", "tonkeeper.com", "vodafone.com.eg",
)
LINK_SHORTENERS = {
    "bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "rb.gy", "shorturl.at", "ow.ly", "goo.gl", "tiny.cc",
    "rebrand.ly", "s.id", "v.gd", "t.ly", "shorte.st", "bl.ink", "buff.ly", "lnkd.in",
}
LINK_RISKY_TLDS = {"xyz", "top", "click", "link", "zip", "mov", "icu", "cyou", "buzz", "rest", "monster", "tk", "ml", "ga", "cf", "gq", "pw", "cam", "vip", "club"}
LINK_BRANDS = ("telegram", "binance", "bybit", "whatsapp", "paypal", "vodafone", "instagram", "facebook", "tiktok", "metamask", "trustwallet", "tonkeeper", "fragment", "google", "apple", "amazon")
LINK_KEYWORDS = ("airdrop", "claim", "verify", "giveaway", "bonus", "walletconnect", "wallet-connect", "connect-wallet", "recover", "seedphrase", "seed-phrase", "prize", "winner")
_URL_RE = re.compile(
    r"(?i)(?:https?://|www\.)[^\s<>\"'«»]+"
    r"|\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:com|net|org|xyz|top|click|link|live|zip|icu|buzz|cyou|rest|monster|tk|ml|ga|cf|gq|info|site|online|store|shop|app|vip|club|cam|ly|gl|cc|to|su|ws|pw|me|io|co)\b(?:/[^\s<>\"'«»]*)?"
)


def _host_of(value):
    target = value if re.match(r"(?i)^[a-z][a-z0-9+.-]*://", value) else "http://" + value
    try:
        return (urlsplit(target).hostname or "").lower().strip(".")
    except ValueError:
        return ""


def analyze_url(raw_url, visible=None):
    """يعيد dict فيه الدرجة والأسباب إذا كان الرابط مشبوهًا، وإلا None. لا يتصل بأي موقع."""
    url = (raw_url or "").strip().rstrip(".,;:!?)]}»\"'")
    if not url:
        return None
    target = url if re.match(r"(?i)^[a-z][a-z0-9+.-]*://", url) else "http://" + url
    try:
        parts = urlsplit(target)
    except ValueError:
        return None
    host = (parts.hostname or "").lower().strip(".")
    if not host:
        return None
    score, reasons = 0, []

    def add(points, reason):
        nonlocal score
        score += points
        reasons.append(reason)

    if "@" in parts.netloc:
        add(3, "الرابط فيه علامة @ لإخفاء وجهته الحقيقية")
    if visible:
        visible_host = _host_of(visible.strip()) if re.search(r"[a-z0-9-]+\.[a-z]{2,}", visible, re.I) else ""
        if visible_host and visible_host != host and not host.endswith("." + visible_host):
            add(3, f"النص الظاهر يشير إلى {visible_host} لكن الوجهة الفعلية مختلفة")
    whitelisted = any(host == d or host.endswith("." + d) for d in LINK_WHITELIST)
    if whitelisted and score == 0:
        return None
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        add(3, "الرابط بعنوان IP مباشر بدل اسم موقع")
    if any(ord(c) > 127 for c in host):
        add(3, "اسم الموقع فيه حروف غير لاتينية (قد يقلّد موقعًا مشهورًا)")
    if "xn--" in host:
        add(3, "اسم الموقع مشفّر بحروف مموهة (punycode)")
    if any(host == d or host.endswith("." + d) for d in LINK_SHORTENERS):
        add(3, "رابط مختصر يخفي الوجهة الحقيقية")
    if host.rsplit(".", 1)[-1] in LINK_RISKY_TLDS:
        add(2, f"امتداد الموقع .{host.rsplit('.', 1)[-1]} كثير الاستخدام في المواقع الاحتيالية")
    if not whitelisted:
        for brand in LINK_BRANDS:
            if brand in host:
                add(3, f"اسم الموقع يقلّد {brand}")
                break
    haystack = (host + parts.path + "?" + parts.query).lower()
    for word in LINK_KEYWORDS:
        if word in haystack:
            add(2, f"يحتوي كلمة مشبوهة ({word})")
            break
    if host.count("-") >= 3:
        add(1, "اسم الموقع فيه شرطات كثيرة")
    if host.count(".") >= 4:
        add(1, "نطاقات فرعية كثيرة")
    if len(host) > 40:
        add(1, "اسم الموقع طويل بشكل غير عادي")
    if url.lower().startswith("http://"):
        add(1, "الرابط غير مؤمّن (http)")
    if score >= 5:
        level = "high"
    elif score >= 3:
        level = "medium"
    else:
        return None
    return {"url": url, "host": host, "score": score, "level": level, "reasons": reasons}


def utf16_slice(text, offset, length):
    data = text.encode("utf-16-le")
    return data[offset * 2:(offset + length) * 2].decode("utf-16-le", errors="ignore")


def extract_links(text, entities):
    found, seen = [], set()

    def push(url, visible=None):
        key = (url or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            found.append((url, visible))

    for ent in entities or []:
        etype = getattr(ent, "type", None)
        if etype == "text_link" and getattr(ent, "url", None):
            push(ent.url, utf16_slice(text, ent.offset, ent.length))
        elif etype == "url":
            push(utf16_slice(text, ent.offset, ent.length))
    for m in _URL_RE.finditer(text or ""):
        push(m.group(0))
    return found


def analyze_message_links(text, entities, limit=3):
    results = [analyze_url(u, v) for u, v in extract_links(text, entities)]
    results = [r for r in results if r]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


async def send_link_alert(bot, owner_id, message):
    try:
        text_raw = message.text or message.caption or ""
        entities = message.entities or message.caption_entities or []
        results = analyze_message_links(text_raw, entities)
        if VIRUSTOTAL_API_KEY and not any(r["level"] == "high" for r in results):
            results = await enrich_with_virustotal(text_raw, entities, results)
        if not results:
            return
        sender = message.from_user or message.chat
        name = getattr(sender, "full_name", None) or getattr(sender, "first_name", None) or "—"
        username = getattr(sender, "username", None)
        sender_id = sender.id
        username_text = f"@{safe_html(username)}" if username else "غير معروف"
        blocks = []
        for r in results:
            level = "🔴 خطير" if r["level"] == "high" else "🟠 مشبوه"
            reasons = "\n".join(f"• {safe_html(x)}" for x in r["reasons"])
            blocks.append(
                f"{E_LANG} <b>Link :</b>\n<blockquote><code>{safe_html(r['url'][:300])}</code></blockquote>\n"
                f"{E_RISK} <b>Risk:</b> {level}\n"
                f"{E_REASONS} <b>Reasons :</b>\n<blockquote>{reasons}</blockquote>"
            )
        card = (
            f"{E_WARN} <b>Suspicious link detected</b>\n\n"
            f"{E_USER} <b>Sender:</b> {safe_html(name)}\n"
            f"{E_USERNAME} <b>Username:</b> {username_text}\n"
            f"{E_ID} <b>User ID:</b> <code>{sender_id}</code>\n\n"
            + "\n\n".join(blocks)
        )
        url = f"https://t.me/{username}" if username else f"tg://user?id={sender_id}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Open Customer Profile", url=url, style="primary")]
        ])
        await bot.send_message(owner_id, card, parse_mode="HTML", reply_markup=kb)
        logger.info("Suspicious link alert sent to %s (%s)", owner_id, results[0]["host"])
    except Exception:
        logger.warning("Failed to send link alert", exc_info=True)


# ─────────────────────── فحص VirusTotal للروابط ───────────────────────

import base64
import shutil
import sys
import tempfile
import time as _time

VT_BASE = "https://www.virustotal.com/api/v3"
VT_CACHE_TTL = 24 * 3600
VT_FAIL_TTL = 300
VT_PER_MIN = 4
VT_DAILY_CAP = 450
VT_MAX_POLLS = 3
VT_POLL_DELAY = 10
VT_MAX_PENDING = 10
LINK_VT_MAX = 3
_VT_CACHE = {}
_VT_STAMPS = []
_VT_DAY = {"date": None, "count": 0}
_VT_STATE = {"block_until": 0.0, "pending": 0, "lock": None}


def vt_url_id(url):
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def is_whitelisted_url(url):
    host = _host_of(url)
    return bool(host) and any(host == d or host.endswith("." + d) for d in LINK_WHITELIST)


async def vt_acquire():
    """ينتظر حتى يتوفر مكان ضمن 4 طلبات/دقيقة. يعيد False إذا انتهت حصة اليوم."""
    while True:
        now = _time.time()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if _VT_DAY["date"] != today:
            _VT_DAY.update(date=today, count=0)
        if _VT_DAY["count"] >= VT_DAILY_CAP:
            return False
        _VT_STAMPS[:] = [t for t in _VT_STAMPS if now - t < 60]
        if len(_VT_STAMPS) < VT_PER_MIN:
            _VT_STAMPS.append(now)
            _VT_DAY["count"] += 1
            return True
        await asyncio.sleep(max(0.5, 60 - (now - _VT_STAMPS[0]) + 0.1))


async def vt_request(method, path, data=None):
    headers = {"x-apikey": VIRUSTOTAL_API_KEY, "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.request(method, VT_BASE + path, data=data) as resp:
            try:
                body = await resp.json(content_type=None)
            except Exception:
                body = None
            return resp.status, body


def vt_summarize(stats, results):
    stats = stats or {}
    malicious = int(stats.get("malicious", 0) or 0)
    suspicious = int(stats.get("suspicious", 0) or 0)
    total = sum(int(v) for v in stats.values() if isinstance(v, (int, float)))
    engines = [
        name for name, info in (results or {}).items()
        if isinstance(info, dict) and info.get("category") in ("malicious", "suspicious")
    ]
    return {"malicious": malicious, "suspicious": suspicious, "total": total, "engines": engines[:3]}


def _vt_handle_status(status):
    """يعيد True إذا كانت الحالة تعني التوقف عن الاستعلام مؤقتًا."""
    if status == 429:
        logger.warning("VirusTotal rate limit reached; pausing for 60s")
        _VT_STATE["block_until"] = _time.time() + 60
        return True
    if status in (401, 403):
        logger.warning("VirusTotal rejected the API key (HTTP %s); pausing for 10 minutes", status)
        _VT_STATE["block_until"] = _time.time() + 600
        return True
    return False


async def _vt_lookup(target, uid):
    if not await vt_acquire():
        logger.warning("VirusTotal daily budget used up")
        return None
    status, body = await vt_request("GET", f"/urls/{uid}")
    if status == 200 and body:
        attrs = (body.get("data") or {}).get("attributes") or {}
        stats = attrs.get("last_analysis_stats") or {}
        if sum(int(v) for v in stats.values() if isinstance(v, (int, float))) > 0:
            return vt_summarize(stats, attrs.get("last_analysis_results"))
    elif status != 404:
        if not _vt_handle_status(status):
            logger.warning("VirusTotal lookup failed with HTTP %s", status)
        return None
    # لا يوجد تقرير: نرسل الرابط للفحص ثم ننتظر النتيجة
    if not await vt_acquire():
        return None
    status, body = await vt_request("POST", "/urls", data={"url": target})
    if status != 200 or not body:
        if not _vt_handle_status(status):
            logger.warning("VirusTotal submit failed with HTTP %s", status)
        return None
    analysis_id = (body.get("data") or {}).get("id")
    if not analysis_id:
        return None
    for _ in range(VT_MAX_POLLS):
        await asyncio.sleep(VT_POLL_DELAY)
        if not await vt_acquire():
            return None
        status, body = await vt_request("GET", f"/analyses/{analysis_id}")
        if status == 200 and body:
            attrs = (body.get("data") or {}).get("attributes") or {}
            if attrs.get("status") == "completed":
                return vt_summarize(attrs.get("stats"), attrs.get("results"))
        elif _vt_handle_status(status):
            return None
    logger.info("VirusTotal analysis for %s did not finish in time", target)
    return None


async def vt_check_url(url):
    """يعيد ملخص VirusTotal (dict) أو None إذا لم يتوفر. النتائج تُحفظ 24 ساعة."""
    if not VIRUSTOTAL_API_KEY or not url:
        return None
    target = url if re.match(r"(?i)^[a-z][a-z0-9+.-]*://", url) else "http://" + url
    uid = vt_url_id(target)
    cached = _VT_CACHE.get(uid)
    if cached and _time.time() < cached[0]:
        return cached[1]
    if _time.time() < _VT_STATE["block_until"]:
        return None
    if _VT_STATE["pending"] >= VT_MAX_PENDING:
        logger.info("VirusTotal queue is full; skipping %s", target)
        return None
    if _VT_STATE["lock"] is None:
        _VT_STATE["lock"] = asyncio.Lock()
    _VT_STATE["pending"] += 1
    try:
        async with _VT_STATE["lock"]:
            cached = _VT_CACHE.get(uid)
            if cached and _time.time() < cached[0]:
                return cached[1]
            try:
                result = await _vt_lookup(target, uid)
            except Exception:
                logger.warning("VirusTotal check failed", exc_info=True)
                result = None
            ttl = VT_CACHE_TTL if result is not None else VT_FAIL_TTL
            _VT_CACHE[uid] = (_time.time() + ttl, result)
            return result
    finally:
        _VT_STATE["pending"] -= 1


def apply_vt(result, url, vt):
    """يدمج نتيجة VirusTotal مع نتيجة الفحص المحلي: محركان فأكثر = خطير، محرك واحد = مشبوه."""
    flagged = vt["malicious"] + vt["suspicious"]
    if flagged <= 0:
        return result
    level = "high" if flagged >= 2 else "medium"
    reason = f"VirusTotal: {flagged} من {vt['total']} محرك أبلغ عن الرابط"
    if vt["engines"]:
        reason += f" ({', '.join(vt['engines'])})"
    if result is None:
        host = _host_of(url)
        return {"url": url, "host": host, "score": flagged, "level": level, "reasons": [reason]}
    result["reasons"].append(reason)
    result["score"] += flagged
    if level == "high":
        result["level"] = "high"
    return result


async def enrich_with_virustotal(text, entities, results):
    by_url = {r["url"]: r for r in results}
    for url, _visible in extract_links(text, entities)[:LINK_VT_MAX]:
        clean = url.strip().rstrip(".,;:!?)]}»\"'")
        if not clean or is_whitelisted_url(clean):
            continue
        vt = await vt_check_url(clean)
        if not vt:
            continue
        merged = apply_vt(by_url.get(clean), clean, vt)
        if merged:
            by_url[clean] = merged
    return sorted(by_url.values(), key=lambda r: r["score"], reverse=True)[:3]


# ───────────────────────── Truecaller lookup ─────────────────────────
async def _tc_start_client():
    global _tc_client
    if _tc_client and _tc_client.is_connected():
        return _tc_client
    if not (TC_API_ID and TC_API_HASH and TC_SESSION):
        return None
    try:
        _tc_client = TelegramClient(StringSession(TC_SESSION), int(TC_API_ID), TC_API_HASH)
        await _tc_client.connect()
        if not await _tc_client.is_user_authorized():
            await _tc_client.disconnect()
            _tc_client = None
            return None
        return _tc_client
    except Exception:
        logger.exception("Truecaller client initialization failed")
        _tc_client = None
        return None


async def _tc_lookup(phone: str):
    async with _tc_lock:
        client = await _tc_start_client()
        if not client:
            return None
        peer = "@" + TC_BOT_USERNAME
        try:
            await client.send_message(peer, phone)
            for _ in range(30):
                await asyncio.sleep(1)
                messages = await client.get_messages(peer, limit=1)
                if not messages:
                    continue
                msg = messages[0]
                body = (msg.raw_text or "").strip()
                if not body or "Searching" in body or "جارٍ البحث" in body:
                    continue
                if any(x in body.lower() for x in ("number:", "country", "name:", "رقم:", "الدولة")):
                    return body
                if "send me any phone number" in body.lower() or "أرسل لي رقم" in body:
                    return None
            return None
        except Exception:
            logger.exception("Truecaller lookup failed")
            return None


def _tc_format(phone: str, raw: str) -> str:
    clean = re.sub(r"[*`_]", "", raw or "")
    def field(pattern):
        m = re.search(pattern, clean, re.I | re.M)
        return html.escape(m.group(1).strip()) if m else "غير متاح"
    number = field(r"(?:Number|رقم)\s*:?\s*([+\d]+)")
    country = field(r"(?:Country|الدولة)\s*:?\s*([^\n]+)")
    carrier = field(r"(?:Carrier|الشبكة)\s*:?\s*([^\n]+)")
    last_seen = field(r"(?:Last Seen|Last seen|آخر ظهور)\s*:?\s*([^\n]+)")
    name = field(r"(?:Name|الاسم)\s*:?\s*([^\n]+)")
    # Keep every result field in its own Telegram blockquote.
    return "\n\n".join([
        f"<blockquote><b>{custom_emoji('🔎', '6203886371363364022')} معلومات الرقم</b></blockquote>",
        f"<blockquote>{custom_emoji('📱', '6203886371363364022')} <b>الرقم:</b> <code>{number if number != 'غير متاح' else html.escape(phone)}</code></blockquote>",
        f"<blockquote>{custom_emoji('🌍', '5336972142066047577')} <b>الدولة:</b> {country}</blockquote>",
        f"<blockquote>{custom_emoji('📶', '6203886371363364022')} <b>الشبكة:</b> {carrier}</blockquote>",
        f"<blockquote>{custom_emoji('🕒', '6206118633370818254')} <b>آخر ظهور:</b> {last_seen}</blockquote>",
        f"<blockquote>{custom_emoji('👤', '6203886371363364022')} <b>الاسم:</b> {name}</blockquote>",
    ])


async def _handle_truecaller_command(message: Message, business_connection_id=None):
    if not business_connection_id:
        if not message.from_user:
            return
        if message.from_user.id != OWNER_ID and await is_bot_user_blocked(message.from_user.id):
            await message.answer("تم حظرك من استخدام البوت.")
            return
        if not await paid_access_allowed(message.from_user.id):
            await send_paid_gate(message)
            return

    async def send_text(text, **kwargs):
        if business_connection_id:
            return await message.bot.send_message(
                chat_id=message.chat.id, text=text,
                business_connection_id=business_connection_id, **kwargs
            )
        return await message.answer(text, **kwargs)

    async def edit_text(sent, text, **kwargs):
        if business_connection_id:
            return await message.bot.edit_message_text(
                chat_id=message.chat.id, message_id=sent.message_id,
                text=text, business_connection_id=business_connection_id, **kwargs
            )
        return await sent.edit_text(text, **kwargs)

    args = (message.text or "").split(maxsplit=1)
    if len(args) != 2:
        await send_text("استخدم الأمر هكذا:\n<code>/tc +201234567890</code>", parse_mode="HTML")
        return
    raw_phone = args[1].strip()
    digits = re.sub(r"\D", "", raw_phone)
    if not raw_phone.startswith("+") or not 7 <= len(digits) <= 15:
        await send_text("أرسل الرقم بالصيغة الدولية، مثال: <code>/tc +201234567890</code>", parse_mode="HTML")
        return
    wait_msg = await send_text(
        f"{custom_emoji('🔎', '6206446249181189526')} جاري البحث... يرجى الانتظار.",
        parse_mode="HTML"
    )
    result = await _tc_lookup(raw_phone)
    if not result:
        await edit_text(wait_msg, "تعذر الحصول على نتيجة. تحقق من إعداد الجلسة أو حاول لاحقًا.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", url=f"https://wa.me/{digits}", style="primary", icon_custom_emoji_id="5231159755803761138"),
         InlineKeyboardButton(text="Telegram", url=f"tg://resolve?phone={digits}", style="primary", icon_custom_emoji_id="6028346797368283073")],
        [InlineKeyboardButton(text="إغلاق", callback_data="tc_close", style="danger", icon_custom_emoji_id="5879895758202735862")]
    ])
    await edit_text(wait_msg, _tc_format(raw_phone, result), reply_markup=keyboard,
                    parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("tc"))
async def truecaller_command(message: Message):
    await _handle_truecaller_command(message)


@router.callback_query(F.data == "tc_close")
async def truecaller_close(call: CallbackQuery):
    try:
        bc_id = getattr(call.message, "business_connection_id", None)
        if bc_id:
            await call.bot.delete_business_messages(
                business_connection_id=bc_id,
                message_ids=[call.message.message_id]
            )
        else:
            await call.message.delete()
    except Exception:
        await call.answer("تعذر إغلاق الرسالة")
    else:
        await call.answer()




# ───────────────────────────── تنزيل الأغاني (يوت) ─────────────────────────────

try:
    from aiogram.types import FSInputFile
except Exception:  # للاختبارات خارج aiogram فقط
    FSInputFile = None

SONG_TIMEOUT = 60
SONG_MAX_PARALLEL = 2
SONG_MAX_BYTES = 48 * 1024 * 1024
# أرقام الإيموجي المميز لكابشن الأغنية: ضع الرقم بدل None لاحقًا، وإن بقي None يظهر الإيموجي العادي
SONG_EMOJI = {
    "title": ("6007938409857815902", "🎧"),
    "artist": ("5909015791088439934", "🎙"),
    "duration": ("5985616167740379273", "⏰"),
    "enjoy": ("6032939483207311182", "✔️"),
}
_SONG_SEM = {"sem": None}
_SONG_CMD_RE = re.compile(r"^يوت\s+(.+)$", re.S)
_AUDIO_EXTS = {".mp3", ".m4a", ".opus", ".webm", ".ogg", ".aac"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


class SongError(Exception):
    pass


def parse_song_command(text):
    match = _SONG_CMD_RE.match((text or "").strip())
    if not match:
        return None
    query = re.sub(r"\s+", " ", match.group(1)).strip()
    if not query or len(query) > 200:
        return None
    return query


def song_target(query):
    if re.match(r"(?i)^https?://\S+$", query):
        return query
    return "ytsearch1:" + query


def fmt_duration(seconds):
    try:
        total = int(round(float(seconds)))
    except (TypeError, ValueError):
        return "—"
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


_YTDLP_COOKIE = {"path": None}


def _ytdlp_cookie_path():
    """cookies اختيارية لتجاوز طلب تسجيل الدخول من يوتيوب على السيرفرات: YTDLP_COOKIES_FILE (مسار) أو YTDLP_COOKIES (المحتوى بصيغة Netscape)."""
    if _YTDLP_COOKIE["path"] is not None:
        return _YTDLP_COOKIE["path"] or None
    path = os.getenv("YTDLP_COOKIES_FILE", "").strip()
    content = os.getenv("YTDLP_COOKIES", "")
    if not path and content.strip():
        try:
            fd, path = tempfile.mkstemp(prefix="ytck_", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content if "\n" in content else content.replace("\\n", "\n"))
        except Exception:
            path = ""
    if path and not os.path.exists(path):
        path = ""
    _YTDLP_COOKIE["path"] = path or ""
    return path or None


def _song_reason(err):
    """يحوّل نص خطأ yt-dlp إلى سبب مختصر يظهر في الشات."""
    e = (err or "").lower()
    for needle, text in (
        ("sign in to confirm", "يوتيوب طلب تسجيل دخول، أضف cookies"),
        ("not a bot", "يوتيوب اعتبر السيرفر بوت، أضف cookies"),
        ("javascript runtime", "يوتيوب يحتاج JS runtime"),
        ("n challenge", "يوتيوب يحتاج JS runtime"),
        ("requested format is not available", "الصيغة غير متاحة"),
        ("http error 403", "يوتيوب رفض التحميل 403"),
        ("ffmpeg", "ffmpeg غير مثبت"),
        ("private video", "الفيديو خاص"),
        ("video unavailable", "الفيديو غير متاح"),
        ("age-restricted", "مقيّد بالعمر"),
        ("confirm your age", "مقيّد بالعمر"),
    ):
        if needle in e:
            return text
    return ""


def build_ytdlp_args(target, outdir, with_ffmpeg):
    args = [
        sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings", "--quiet", "--no-progress",
        "--socket-timeout", "15", "--retries", "2", "--max-filesize", "45M",
        "--write-info-json", "--no-write-playlist-metafiles", "-o", os.path.join(outdir, "%(id)s.%(ext)s"),
    ]
    _ck = _ytdlp_cookie_path()
    if _ck:
        args += ["--cookies", _ck]
    _js = os.getenv("YTDLP_JS_RUNTIME", "").strip()
    if _js:
        args += ["--js-runtimes", _js]
    if with_ffmpeg:
        args += ["-f", "bestaudio/best", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                 "--write-thumbnail", "--convert-thumbnails", "jpg"]
    else:
        args += ["-f", "bestaudio[ext=m4a]/bestaudio"]
    args.append(target)
    return args


async def run_cmd(args, timeout=None):
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    finally:
        if proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
    return proc.returncode, out.decode("utf-8", "ignore"), err.decode("utf-8", "ignore")


def find_song_files(outdir):
    """يختار ملفات الأغنية نفسها: الغلاف وملف المعلومات اللذان يحملان نفس اسم ملف الصوت."""
    paths = sorted(Path(outdir).iterdir())
    audio = next((p for p in paths if p.suffix.lower() in _AUDIO_EXTS), None)
    stem = audio.stem if audio else None
    infos = [p for p in paths if p.name.lower().endswith(".info.json")]
    images = [p for p in paths if p.suffix.lower() in _IMAGE_EXTS and "thumb_small" not in p.name.lower()]
    info = next((p for p in infos if stem and p.name[:-len(".info.json")] == stem), None)
    if info is None:
        # لا يوجد ملف بنفس الاسم: نفضّل ما يحتوي بيانات الفيديو (المدة) على ملف قائمة البحث
        for candidate in infos:
            try:
                with open(candidate, encoding="utf-8") as fh:
                    if json.load(fh).get("duration") is not None:
                        info = candidate
                        break
            except Exception:
                continue
        if info is None and infos:
            info = infos[0]
    thumb = next((p for p in images if stem and p.stem == stem), None) or (images[0] if images else None)
    return {"audio": str(audio) if audio else None, "thumb": str(thumb) if thumb else None,
            "info": str(info) if info else None}


def read_song_info(path):
    try:
        with open(path, encoding="utf-8") as fh:
            info = json.load(fh)
    except Exception:
        return {}
    entries = info.get("entries")
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        info = entries[0]
    return {
        "title": info.get("track") or info.get("title") or "",
        "artist": info.get("artist") or info.get("channel") or info.get("uploader") or "",
        "duration": info.get("duration"),
    }


async def make_thumbnail(src, dst):
    """يصغّر الغلاف بما يناسب تيليجرام: JPEG وأبعاده 320 فأقل وحجمه أقل من 200 كيلوبايت."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    for quality in (4, 8, 14, 22):
        code, _out, _err = await run_cmd(
            [ffmpeg, "-y", "-loglevel", "error", "-i", src,
             "-vf", "scale=320:320:force_original_aspect_ratio=decrease",
             "-frames:v", "1", "-q:v", str(quality), dst], 20)
        if code == 0 and os.path.exists(dst) and os.path.getsize(dst) <= 190 * 1024:
            return True
    return False


async def song_download(query, tmpdir):
    with_ffmpeg = bool(shutil.which("ffmpeg"))
    _code, _out, err = await run_cmd(build_ytdlp_args(song_target(query), tmpdir, with_ffmpeg), SONG_TIMEOUT)
    files = find_song_files(tmpdir)
    if not files["audio"]:
        logger.warning("yt-dlp produced no audio file for %r: %s", query, err.strip()[-600:])
        _why = _song_reason(err)
        raise SongError(("تعذر جلب معلومات الرابط" if not files["info"] else "تعذر تحميل الملف") + (f" ({_why})" if _why else ""))
    info = read_song_info(files["info"]) if files["info"] else {}
    if os.path.getsize(files["audio"]) > SONG_MAX_BYTES:
        raise SongError("حجم الملف كبير")
    thumb = None
    if files["thumb"]:
        small = os.path.join(tmpdir, "thumb_small.jpg")
        if await make_thumbnail(files["thumb"], small):
            thumb = small
    return {"audio": files["audio"], "thumb": thumb, **info}


def song_emoji_entities(text_parts):
    """يبني نص الكابشن وكيانات الإيموجي المميز. text_parts: قائمة من (نص) أو ("emoji", المفتاح)."""
    text, entities = "", []
    for part in text_parts:
        if isinstance(part, tuple):
            emoji_id, fallback = SONG_EMOJI[part[1]]
            if emoji_id:
                entities.append(MessageEntity(type="custom_emoji", offset=utf16_len(text),
                                              length=utf16_len(fallback), custom_emoji_id=emoji_id))
            text += fallback
        else:
            text += part
    return text, entities


def build_song_caption(title, artist, duration):
    title = (title or "—").strip()[:200]
    artist = (artist or "—").strip()[:100]
    text, entities = song_emoji_entities([
        ("emoji", "title"), f" {title}\n\n",
        ("emoji", "artist"), f" {artist}\n\n",
        ("emoji", "duration"), f" {fmt_duration(duration)}\n\n",
        ("emoji", "enjoy"), " إنبـسط يا بـرو",
    ])
    # حرف غير مرئي بتنسيق خاص: وجود entities يمنع تغليف الكابشن بالاقتباس
    entities.append(MessageEntity(type="bold", offset=utf16_len(text), length=1))
    return text + "\u200b", entities


async def _song_fail(bot, bc_id, chat_id, status_id, reason):
    text = f"تعذر تنفيذ التحميل: {reason}"
    try:
        await bot.edit_message_text(text=text, chat_id=chat_id, message_id=status_id, business_connection_id=bc_id)
    except Exception:
        try:
            await bot.send_message(chat_id=chat_id, text=text, business_connection_id=bc_id)
        except Exception:
            logger.warning("Could not report song failure", exc_info=True)


async def run_song_job(bot, bc_id, chat_id, query, status_id):
    tmpdir = tempfile.mkdtemp(prefix="song_")
    try:
        if _SONG_SEM["sem"] is None:
            _SONG_SEM["sem"] = asyncio.Semaphore(SONG_MAX_PARALLEL)
        async with _SONG_SEM["sem"]:
            try:
                data = await asyncio.wait_for(song_download(query, tmpdir), SONG_TIMEOUT)
            except asyncio.TimeoutError:
                raise SongError("انتهت المهلة")
        caption, entities = build_song_caption(data.get("title"), data.get("artist"), data.get("duration"))
        kwargs = {
            "chat_id": chat_id, "audio": FSInputFile(data["audio"]), "caption": caption,
            "caption_entities": entities, "parse_mode": None, "business_connection_id": bc_id,
            "title": (data.get("title") or "")[:64] or None, "performer": (data.get("artist") or "")[:64] or None,
        }
        if data.get("duration"):
            kwargs["duration"] = int(round(float(data["duration"])))
        if data.get("thumb"):
            kwargs["thumbnail"] = FSInputFile(data["thumb"])
        await bot.send_audio(**kwargs)
        await delete_biz_msg(bot, bc_id, chat_id, status_id)
    except SongError as exc:
        await _song_fail(bot, bc_id, chat_id, status_id, str(exc))
    except Exception:
        logger.warning("Song job failed", exc_info=True)
        await _song_fail(bot, bc_id, chat_id, status_id, "حدث خطأ غير متوقع")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


async def maybe_start_song(message, bc_id):
    query = parse_song_command(message.text)
    if not query:
        return False
    try:
        status = await message.bot.send_message(
            chat_id=message.chat.id, text="جار البحث...", business_connection_id=bc_id
        )
    except Exception:
        logger.warning("Could not start song search", exc_info=True)
        return False
    await delete_biz_msg(message.bot, bc_id, message.chat.id, message.message_id)
    spawn(run_song_job(message.bot, bc_id, message.chat.id, query, status.message_id))
    return True


# ═══════════════════════════ نهاية الميزات الإضافية ═══════════════════════════


def _is_own_business_message(message: Message, owner_id: int) -> bool:
    """True for messages authored by the account owner or this bot."""
    sender = getattr(message, "from_user", None)
    if sender and (sender.id == owner_id or getattr(sender, "is_bot", False)):
        return True
    # Telegram may identify a message sent on behalf of the connected business bot
    # separately from `from_user`.
    if getattr(message, "sender_business_bot", None) is not None:
        return True
    return False


@router.edited_business_message()
async def edited_business_message(message: Message):
    bc_id = message.business_connection_id
    if not bc_id or not message.chat:
        return

    conn = await db()
    biz = await fetchone(conn,
        "SELECT user_id FROM business WHERE connection_id=?", (bc_id,))
    if not biz:
        await conn.close()
        return

    owner_id = biz["user_id"]
    # Track customer edits only. Edits made by the owner or the bot itself
    # must never create a log entry or a private notification.
    if _is_own_business_message(message, owner_id):
        await conn.close()
        return
    if not (await get_account_setting(owner_id, "track_edited_enabled") or 0):
        await conn.close(); return

    old = await fetchone(conn,
        "SELECT text_content FROM tracked_messages WHERE connection_id=? AND chat_id=? AND message_id=?",
        (bc_id, message.chat.id, message.message_id))

    old_text = old["text_content"] if old else "(غير معروف)"

  
    new_text = message.html_text or message.text or message.caption or ""
    await conn.execute("""
        INSERT INTO tracked_messages(connection_id, chat_id, message_id, sender_id,
        sender_name, sender_username, text_content, media_type, media_file_id, created_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(connection_id, chat_id, message_id) DO UPDATE SET
        text_content=excluded.text_content
    """, (
        bc_id, message.chat.id, message.message_id,
        message.from_user.id if message.from_user else message.chat.id,
        message.from_user.first_name if message.from_user else "",
        message.from_user.username if message.from_user else "",
        new_text, "", "", datetime.now(timezone.utc).isoformat()
    ))
    await conn.execute("INSERT INTO tracking_logs(owner_id,connection_id,chat_id,message_id,event_type,old_text,new_text,media_type,media_file_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (biz["user_id"],bc_id,message.chat.id,message.message_id,"edited",old_text,new_text,"","",datetime.now(timezone.utc).isoformat()))
    await conn.commit()
    await conn.close()

    sender_name = message.from_user.first_name if message.from_user else ""
    sender_username = message.from_user.username if message.from_user else ""
    sender_id = message.from_user.id if message.from_user else message.chat.id
    if sender_id == owner_id:
        return

    txt = (
        "<tg-emoji emoji-id='5771847914477326786'>✏️</tg-emoji> <b>تم تعديل رسالة</b>\n\n"
        f"{tracking_identity(sender_name, sender_username, sender_id)}\n\n"
        f"<tg-emoji emoji-id='6030622631818956594'>💬</tg-emoji> قبل التعديل:\n{old_text or '(بدون نص)'}\n\n"
        f"<tg-emoji emoji-id='6030784887093464891'>💬</tg-emoji> بعد التعديل:\n{new_text or '(بدون نص)'}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="فتح بروفايل العميل",
            url=f"tg://user?id={sender_id}", style="primary",
            icon_custom_emoji_id="5452085950022707790"
        )]
    ])
    try:
        await message.bot.send_message(
            chat_id=owner_id, text=txt, reply_markup=kb, parse_mode="HTML")
    except Exception:
        logger.exception("Failed to send edit notice")

print("""

╔══════════════════════════════════════════════════════════╗
║                        E L   Z O Z                       ║
║                   TELEGRAM BUSINESS BOT                  ║
║                     DEV BY : @Z0_E0                      ║
╚══════════════════════════════════════════════════════════╝
""")

@router.deleted_business_messages()
async def deleted_business_messages(update: BusinessMessagesDeleted):
    bc_id = update.business_connection_id
    if not bc_id or not update.chat:
        return

    conn = await db()
    biz = await fetchone(conn,
        "SELECT user_id FROM business WHERE connection_id=?", (bc_id,))
    if not biz:
        await conn.close()
        return

    owner_id = biz["user_id"]
    if not (await get_account_setting(owner_id, "track_deleted_enabled") or 0):
        await conn.close(); return
    try:
        bot_id = (await update.bot.me()).id
    except Exception:
        bot_id = None

    for msg_id in update.message_ids:
        row = await fetchone(conn,
            "SELECT * FROM tracked_messages WHERE connection_id=? AND chat_id=? AND message_id=?",
            (bc_id, update.chat.id, msg_id))
        if not row:
            continue

        sender_name = row["sender_name"] or ""
        sender_username = row["sender_username"] or ""
        sender_id = row["sender_id"] or update.chat.id
        # The Business API can report deletions of messages sent by the bot too.
        # Remove those cached rows silently; only customer-initiated deletions
        # should generate an alert for the account owner.
        if sender_id == owner_id or (bot_id is not None and sender_id == bot_id):
            await conn.execute("DELETE FROM tracked_messages WHERE id=?", (row["id"],))
            continue
        text_content = row["text_content"] or ""
        media_type = row["media_type"] or ""
        media_file_id = row["media_file_id"] or ""

        last_row = await fetchone(conn,
            "SELECT text_content, media_type FROM tracked_messages "
            "WHERE connection_id=? AND chat_id=? AND message_id<>? AND sender_id=? "
            "ORDER BY created_at DESC LIMIT 1",
            (bc_id, update.chat.id, msg_id, sender_id))
        deleted_display = tracked_message_display(text_content, media_type)
        last_text = tracked_message_display(
            last_row["text_content"], last_row["media_type"]
        ) if last_row else "(لا توجد رسالة سابقة)"
        txt = (
            "<tg-emoji emoji-id='5873044297523140571'>🗑️</tg-emoji> <b>تم حذف رسالة</b>\n\n"
            f"{tracking_identity(sender_name, sender_username, sender_id)}\n\n"
            f"<tg-emoji emoji-id='6030512294109122096'>💬</tg-emoji> الرسالة المحذوفة:\n{deleted_display}\n\n"
            f"<tg-emoji emoji-id='6030512294109122096'>💬</tg-emoji> آخر رسالة بعتها:\n{last_text}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="فتح بروفايل العميل",
                url=f"tg://user?id={sender_id}", style="primary",
                icon_custom_emoji_id="5452085950022707790"
            )]
        ])

        await conn.execute("INSERT INTO tracking_logs(owner_id,connection_id,chat_id,message_id,event_type,old_text,new_text,media_type,media_file_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (owner_id,bc_id,update.chat.id,msg_id,"deleted",text_content,"",media_type,media_file_id,datetime.now(timezone.utc).isoformat()))

        try:
            if media_file_id:
                if media_type == "photo":
                    await update.bot.send_photo(chat_id=owner_id, photo=media_file_id)
                elif media_type == "video":
                    await update.bot.send_video(chat_id=owner_id, video=media_file_id)
                elif media_type == "voice":
                    await update.bot.send_voice(chat_id=owner_id, voice=media_file_id)
                elif media_type == "audio":
                    await update.bot.send_audio(chat_id=owner_id, audio=media_file_id)
                elif media_type == "document":
                    await update.bot.send_document(chat_id=owner_id, document=media_file_id)
                elif media_type == "animation":
                    await update.bot.send_animation(chat_id=owner_id, animation=media_file_id)
                elif media_type == "sticker":
                    await update.bot.send_sticker(chat_id=owner_id, sticker=media_file_id)
        except Exception:
            logger.exception("Failed to send deleted media")

  
        try:
            await update.bot.send_message(
                chat_id=owner_id, text=txt, reply_markup=kb, parse_mode="HTML")
        except Exception:
            logger.exception("Failed to send delete notice")

      
        await conn.execute("DELETE FROM tracked_messages WHERE id=?", (row["id"],))

    await conn.commit()
    await conn.close()

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
@router.business_message(
    F.photo | F.video | F.voice | F.audio | F.document | F.animation |
    F.sticker | F.text | F.caption
)
async def track_incoming(message: Message):
    bc_id = message.business_connection_id
    if not bc_id or not message.chat:
        return
    # Cache only messages sent by real users. Never cache the bot's own
    # outgoing Business messages, otherwise their later deletion is mistaken
    # for a customer deletion.
    sender = getattr(message, "from_user", None)
    if sender and getattr(sender, "is_bot", False):
        return
    if getattr(message, "sender_business_bot", None) is not None:
        return

    conn = await db()
    biz = await fetchone(conn,
        "SELECT user_id FROM business WHERE connection_id=?", (bc_id,))
    if not biz:
        await conn.close()
        return

    # Ignore messages authored by the connected account owner (including
    # messages sent by the owner/admin through the connected Business bot).
    # Only the other person in the Business chat is eligible for tracking.
    if _is_own_business_message(message, int(biz["user_id"])):
        await conn.close()
        return

    if not ((await get_account_setting(biz["user_id"], "track_deleted_enabled") or 0) or (await get_account_setting(biz["user_id"], "track_edited_enabled") or 0)):
        await conn.close(); return
    text = message.html_text or message.text or message.caption or ""
    media_type = ""
    media_file_id = ""
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_file_id = message.video.file_id
    elif message.voice:
        media_type = "voice"
        media_file_id = message.voice.file_id
    elif message.audio:
        media_type = "audio"
        media_file_id = message.audio.file_id
    elif message.document:
        media_type = "document"
        media_file_id = message.document.file_id
    elif message.animation:
        media_type = "animation"
        media_file_id = message.animation.file_id
    elif message.sticker:
        media_type = "sticker"
        media_file_id = message.sticker.file_id

    await conn.execute("""
        INSERT OR REPLACE INTO tracked_messages(
            connection_id, chat_id, message_id, sender_id,
            sender_name, sender_username, text_content,
            media_type, media_file_id, created_at
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bc_id, message.chat.id, message.message_id,
        message.from_user.id if message.from_user else message.chat.id,
        message.from_user.first_name if message.from_user else "",
        message.from_user.username if message.from_user else "",
        text, media_type, media_file_id, datetime.now(timezone.utc).isoformat()
    ))
    await conn.commit()
    await conn.close()

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
def parse_transfer_request(value):
    match = re.fullmatch(r"\s*(\+?[0-9][0-9\s\-]{5,18}[0-9])\s+([0-9]+(?:[.,][0-9]{1,2})?)\s*", value or "")
    if not match:
        return None
    phone = re.sub(r"[\s\-]", "", match.group(1))
    digits = phone[1:] if phone.startswith("+") else phone
    if not 7 <= len(digits) <= 15:
        return None
    amount = match.group(2).replace(",", ".")
    if "." in amount:
        amount = amount.rstrip("0").rstrip(".")
    return phone, amount


def transfer_codes(phone, amount):
    return {
        "etisalat": f"*777*1*{phone}*{amount}#",
        "orange": f"#7115*1*1*1*{phone}*{amount}#",
        "vodafone": f"*9*7*{phone}*{amount}#",
    }


def transfer_codes_kb(codes):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Vodafone Code", copy_text=CopyTextButton(text=codes["vodafone"]),
            style="primary"
        )],
        [InlineKeyboardButton(
            text="Orange Code", copy_text=CopyTextButton(text=codes["orange"]),
            style="primary"
        )],
        [InlineKeyboardButton(
            text="Etisalat Code", copy_text=CopyTextButton(text=codes["etisalat"]),
            style="primary"
        )],
    ])


def transfer_codes_text(phone, amount, codes):
    return (
        f"<blockquote><b>Transfer codes for: <code>{phone}</code></b></blockquote>\n"
        f"<blockquote><b>Amount: {amount} EGP</b></blockquote>\n"
        "<blockquote>Click the buttons below to copy the transfer codes.</blockquote>"
    )


async def send_transfer_codes(target, phone, amount, business_connection_id=None):
    codes = transfer_codes(phone, amount)
    kwargs = {
        "chat_id": target.chat.id,
        "text": transfer_codes_text(phone, amount, codes),
        "reply_markup": transfer_codes_kb(codes),
        "parse_mode": "HTML",
    }
    if business_connection_id:
        kwargs["business_connection_id"] = business_connection_id
    return await target.bot.send_message(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# RICH MESSAGE LAYER — Telegram Bot API 10.1+ (sendRichMessage / tg-button)
# طبقة مركزية واحدة: كل رسالة تحتوي InlineKeyboardMarkup تمر من هنا تلقائيًا
# (Send/Edit/EditReplyMarkup) عبر middleware على جلسة البوت، دون تغيير الـHandlers.
# ═══════════════════════════════════════════════════════════════════════════
import time as _rtime
from collections import OrderedDict as _ROrderedDict
from html.parser import HTMLParser as _RHTMLParser
from typing import Any as _RAny, Dict as _RDict, Optional as _ROptional, Union as _RUnion

from aiogram.methods.base import TelegramMethod as _RTelegramMethod
from aiogram.types import Message as _RMessage, ReplyParameters as _RReplyParameters
from aiogram.client.default import Default as _RDefault
from aiogram.exceptions import (
    TelegramAPIError as _RAPIError,
    TelegramBadRequest as _RBadRequest,
    TelegramForbiddenError as _RForbidden,
    TelegramNetworkError as _RNetworkError,
    TelegramNotFound as _RNotFound,
    TelegramRetryAfter as _RRetryAfter,
    TelegramServerError as _RServerError,
)

rich_logger = logging.getLogger("nexus_bot.rich")

# ───────── إعدادات (من .env، لا تغيّر أي إعداد موجود) ─────────
RICH_ENABLED = os.getenv("RICH_MESSAGES", "1").strip().lower() not in ("0", "false", "off", "no")
# إرسال (صورة/فيديو/صوت + أزرار) كرسالة Rich عبر tg://photo?id=… — مُعطّل افتراضيًا لأنه غير مُجرَّب فعليًا.
RICH_MEDIA = os.getenv("RICH_MEDIA", "0").strip().lower() in ("1", "true", "on", "yes")
RICH_NOTIFY = os.getenv("RICH_NOTIFY", "1").strip().lower() not in ("0", "false", "off", "no")
RICH_UNSUPPORTED_SECONDS = 3600     # حساب/محادثة لا تدعم Rich (غير مميز): نتخطاها ساعة ثم نعيد المحاولة
RICH_PROBE = os.getenv("RICH_PROBE", "0").strip().lower() in ("1", "true", "on", "yes")
RICH_BTN_FALLBACK_EMOJI = "⭐"        # لازم يكون إيموجي حقيقي (رمز عادي مثل • يرفضه الخادم) — نفس ما اشتغل في نسختك التجريبية
RICH_STYLES = ("primary", "success", "danger")
RICH_MAX_BUTTONS_PER_ROW = 8
RICH_BREAKER_THRESHOLD = 3           # عدد الرفض المتتالي قبل إيقاف Rich مؤقتًا لنطاق معيّن
RICH_BREAKER_SECONDS = 600
RICH_CACHE_LIMIT = 4000

_RICH_BREAKER = {}                   # scope -> {"fail": int, "until": float}
_RICH_BODY_CACHE = _ROrderedDict()   # (chat_id, message_id) -> body html (بدون أزرار)
_RICH_UNSUPPORTED = {}             # مفتاح الحساب/المحادثة -> وقت انتهاء التخطّي
_RICH_STATS = {"account_unsupported": 0, "ok": 0, "fallback": 0, "skipped": 0, "chat_errors": 0, "passthrough": 0, "unsupported": 0}
_RICH_FIRST_OK = {"logged": False}
_RICH_RT = {"enabled": RICH_ENABLED, "notify": RICH_NOTIFY}   # قابلة للتبديل من لوحة الأدمن وتُحفظ في القاعدة
_RICH_PERSIST = {"task": None}


def _rstat(name):
    _RICH_STATS[name] = _RICH_STATS.get(name, 0) + 1
    _rich_persist_soon()


def _rich_persist_soon():
    t = _RICH_PERSIST["task"]
    if t is not None and not t.done():
        return
    try:
        _RICH_PERSIST["task"] = asyncio.get_running_loop().create_task(_rich_persist_run())
    except RuntimeError:
        pass


async def _rich_persist_run():
    await asyncio.sleep(20)            # تجميع التحديثات: كتابة واحدة كل 20 ثانية بحد أقصى
    await rich_state_save_now()


async def rich_state_save_now():
    try:
        await set_bot_message("__rich_stats__", json.dumps(_RICH_STATS))
        await set_bot_message("__rich_cfg__", json.dumps(_RICH_RT))
    except Exception:
        rich_logger.debug("تعذر حفظ إحصاءات Rich", exc_info=True)


async def rich_state_load():
    try:
        stats = json.loads(await get_bot_message("__rich_stats__") or "{}")
        for k in list(_RICH_STATS):
            _RICH_STATS[k] = int(stats.get(k, 0))
        cfg = json.loads(await get_bot_message("__rich_cfg__") or "{}")
        for k in ("enabled", "notify"):
            if k in cfg:
                _RICH_RT[k] = bool(cfg[k])
    except Exception:
        rich_logger.warning("تعذر تحميل إحصاءات/إعدادات Rich المحفوظة؛ ستبدأ من الصفر.", exc_info=True)
_RICH_CAPS = {"br": True}           # يُضبط تلقائيًا من الفحص (RICH_PROBE=1): هل الخادم يقبل <br>؟


_RICH_NOTIFIED = {}


def _rich_notify(bot, title, reason, snippet=""):
    """يرسل للمالك سبب فشل Rich على تليجرام (مرة كل 5 دقائق لكل سبب) — للتشخيص بدون فتح الـConsole."""
    try:
        if not _RICH_RT["notify"]:
            return
        key = f"{title}|{str(reason)[:80]}"
        now = _rtime.time()
        if now - _RICH_NOTIFIED.get(key, 0) < 1800:
            return
        _RICH_NOTIFIED[key] = now
        msg = f"⚠️ Rich: {title}\nالسبب: {html.escape(str(reason))[:600]}"
        if snippet:
            msg += f"\nHTML: {html.escape(snippet)[:300]}"
        asyncio.get_running_loop().create_task(_rich_notify_send(bot, msg))
    except Exception:
        pass


async def _rich_notify_send(bot, msg):
    try:
        await bot.send_message(OWNER_ID, msg, parse_mode=None)
    except Exception:
        rich_logger.debug("تعذر إرسال إخطار Rich للمالك", exc_info=True)


class _RichUnsupported(Exception):
    """بنية لا يمكن تمثيلها كـRich دون فقدان وظيفة → تبقى الرسالة بالطريقة الكلاسيكية (مع تسجيل السبب)."""


# ───────── تحويل HTML الكلاسيكي (parse_mode=HTML) إلى Rich HTML ─────────
# في Rich HTML السطر الجديد "\n" مجرد مسافة، لذلك: فقرة جديدة = <p>، وسطر جديد = <br>.
_INLINE_MAP = {
    "b": "b", "strong": "b", "i": "i", "em": "i", "u": "u", "ins": "u",
    "s": "s", "strike": "s", "del": "s", "tg-spoiler": "tg-spoiler",
}


def _rx_escape(text):
    return html.escape(text, quote=False)


def _rx_attr(value):
    return html.escape(str(value), quote=True)


class _TgHtmlToRich(_RHTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.inline = []        # [(rich_open_tag, rich_name)]
        self.p_open = False
        self.in_quote = False
        self.in_pre = False
        self.use_br = _RICH_CAPS.get("br", True)

    # --- فقرات ---
    def _open_p(self):
        if self.in_pre or self.p_open or (self.in_quote and self.use_br):
            return
        self.out.append("<p>")
        self.p_open = True
        for open_tag, _ in self.inline:
            self.out.append(open_tag)

    def _close_p(self):
        if not self.p_open:
            return
        for _, name in reversed(self.inline):
            self.out.append(f"</{name}>")
        self.out.append("</p>")
        self.p_open = False

    def _emit_text(self, text):
        if not text:
            return
        if self.in_pre:
            self.out.append(_rx_escape(text))
            return
        if self.in_quote and self.use_br:
            text = re.sub(r"\n{3,}", "\n\n", text)
            self.out.append(_rx_escape(text).replace("\n", "<br>"))
            return
        for part in re.split(r"(\n{2,})" if self.use_br else r"(\n+)", text):
            if not part:
                continue
            if part.startswith("\n"):
                self._close_p()
                continue
            if not self.p_open and not part.strip():
                continue
            self._open_p()
            self.out.append(_rx_escape(part).replace("\n", "<br>"))

    # --- وسوم ---
    def handle_data(self, data):
        self._emit_text(data)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag == "br":
            self._emit_text("\n")
            return
        if tag == "blockquote":
            self._close_p()
            self.out.append("<blockquote>")
            self.in_quote = True
            return
        if tag == "pre":
            self._close_p()
            self.out.append("<pre>")
            self.in_pre = True
            return
        if tag == "code":
            cls = a.get("class", "")
            if self.in_pre:
                self.out.append(f'<code class="{_rx_attr(cls)}">' if cls else "<code>")
                self.inline.append(("", "code"))
                return
            self._open_p()
            self.out.append("<code>")
            self.inline.append(("<code>", "code"))
            return
        if tag == "a":
            href = a.get("href", "")
            if not href:
                self._emit_text(self.get_starttag_text() or "")
                return
            open_tag = f'<a href="{_rx_attr(href)}">'
            self._open_p()
            self.out.append(open_tag)
            self.inline.append((open_tag, "a"))
            return
        if tag == "tg-emoji":
            eid = a.get("emoji-id", "")
            if not eid:
                self._emit_text(self.get_starttag_text() or "")
                return
            open_tag = f'<tg-emoji emoji-id="{_rx_attr(eid)}">'
            self._open_p()
            self.out.append(open_tag)
            self.inline.append((open_tag, "tg-emoji"))
            return
        if tag == "span" and "tg-spoiler" in a.get("class", ""):
            self._open_p()
            self.out.append("<tg-spoiler>")
            self.inline.append(("<tg-spoiler>", "tg-spoiler"))
            return
        name = _INLINE_MAP.get(tag)
        if name and not self.in_pre:
            open_tag = f"<{name}>"
            self._open_p()
            self.out.append(open_tag)
            self.inline.append((open_tag, name))
            return
        self._emit_text(self.get_starttag_text() or "")

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "br":
            self._emit_text("\n")
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "blockquote" and self.in_quote:
            self._close_p()
            self.out.append("</blockquote>")
            self.in_quote = False
            return
        if tag == "pre" and self.in_pre:
            self.out.append("</pre>")
            self.in_pre = False
            return
        if tag == "span":
            tag = "tg-spoiler-span"
        wanted = {"code": "code", "a": "a", "tg-emoji": "tg-emoji", "tg-spoiler-span": "tg-spoiler"}.get(tag) or _INLINE_MAP.get(tag)
        if not wanted:
            return
        for idx in range(len(self.inline) - 1, -1, -1):
            if self.inline[idx][1] == wanted:
                for _, name in reversed(self.inline[idx:]):
                    self.out.append(f"</{name}>")
                del self.inline[idx:]
                return

    def finish(self):
        self.close()
        for _, name in reversed(self.inline):
            self.out.append(f"</{name}>")
        self.inline = []
        if self.in_pre:
            self.out.append("</pre>")
            self.in_pre = False
        if self.in_quote:
            self.out.append("</blockquote>")
            self.in_quote = False
        self.p_open = False
        # إغلاق فقرة مفتوحة (الوسوم الداخلية أُغلقت أعلاه)
        res = "".join(self.out)
        opens = res.count("<p>") - res.count("</p>")
        if opens > 0:
            res += "</p>" * opens
        return res


def tg_html_to_rich(text):
    """يحوّل نص parse_mode=HTML الكلاسيكي إلى HTML صالح لـsendRichMessage مع حفظ الإيموجي المميز."""
    parser = _TgHtmlToRich()
    parser.feed(text or "")
    res = parser.finish()
    res = re.sub(r"<p>(?:\s|<br>)*</p>", "", res)
    res = re.sub(r"<p>(?:<br>)+", "<p>", res)
    res = re.sub(r"(?:<br>)+</p>", "</p>", res)
    res = re.sub(r"<blockquote>(?:<br>)+", "<blockquote>", res)
    res = re.sub(r"(?:<br>)+</blockquote>", "</blockquote>", res)
    return res


def plain_to_rich(text):
    return tg_html_to_rich(_rx_escape(text or ""))


# ───────── تحويل InlineKeyboardMarkup إلى <tg-button-row> ─────────
_BAD_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def _clean_button_url(value):
    """إزالة محارف Unicode غير المرئية التي تُفسد روابط الأزرار، مثل U+2060."""
    raw = str(value or "")
    cleaned = "".join(
        ch for ch in raw
        if unicodedata.category(ch) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}
    )
    return cleaned.strip()


def _valid_button_url(value):
    value = _clean_button_url(value)
    if not value or any(ch.isspace() for ch in value):
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https", "tg"}:
        return False
    if parsed.scheme in {"http", "https"}:
        return bool(parsed.netloc)
    return bool(parsed.netloc or parsed.path)


def rich_button_html(btn):
    text = (getattr(btn, "text", "") or "").strip()
    if not text:
        raise _RichUnsupported("زر بدون نص")
    cb = getattr(btn, "callback_data", None)
    url = getattr(btn, "url", None)
    copy_obj = getattr(btn, "copy_text", None)
    if cb is not None:
        if not cb or len(cb.encode("utf-8")) > 64:
            raise _RichUnsupported(f"callback_data خارج 1-64 بايت: {cb!r}")
        if _BAD_CTRL.search(cb):
            raise _RichUnsupported(f"callback_data يحتوي محارف تحكم: {cb!r}")
        attrs = f'type="callback_data" data="{_rx_attr(cb)}"'
    elif url:
        clean_url = _clean_button_url(url)
        if not _valid_button_url(clean_url):
            raise _RichUnsupported(f"رابط غير صالح بعد تنظيف المحارف الخفية: {url!r}")
        attrs = f'type="url" url="{_rx_attr(clean_url)}"'
    elif copy_obj is not None and getattr(copy_obj, "text", None):
        attrs = f'type="copy_text" text="{_rx_attr(copy_obj.text)}"'
    else:
        raise _RichUnsupported("نوع زر غير مدعوم في Rich (web_app/switch_inline/login_url/pay…)")
    style = getattr(btn, "style", None)
    if style in RICH_STYLES:
        attrs += f' style="{style}"'
    label = _rx_escape(text)
    icon = getattr(btn, "icon_custom_emoji_id", None)
    if icon:
        label = f'<tg-emoji emoji-id="{_rx_attr(icon)}">{RICH_BTN_FALLBACK_EMOJI}</tg-emoji> {label}'
    return f"<tg-button {attrs}>{label}</tg-button>"


def markup_to_rich_html(markup):
    rows = getattr(markup, "inline_keyboard", None) or []
    parts = []
    for row in rows:
        row = list(row or [])
        for i in range(0, len(row), RICH_MAX_BUTTONS_PER_ROW):
            chunk = row[i:i + RICH_MAX_BUTTONS_PER_ROW]
            if chunk:
                parts.append("<tg-button-row>" + "".join(rich_button_html(b) for b in chunk) + "</tg-button-row>")
    if not parts:
        raise _RichUnsupported("لوحة أزرار فارغة")
    return "".join(parts)


# ───────── طرق Bot API (نعرّفها محليًا لتعمل مع أي إصدار Aiogram) ─────────
class SendRichMessage(_RTelegramMethod[_RMessage]):
    __returning__ = _RMessage
    __api_method__ = "sendRichMessage"

    chat_id: _RUnion[int, str]
    rich_message: _RDict[str, _RAny]
    business_connection_id: _ROptional[str] = None
    message_thread_id: _ROptional[int] = None
    direct_messages_topic_id: _ROptional[int] = None
    disable_notification: _ROptional[bool] = None
    protect_content: _ROptional[bool] = None
    allow_paid_broadcast: _ROptional[bool] = None
    message_effect_id: _ROptional[str] = None
    reply_parameters: _ROptional[_RReplyParameters] = None


class EditRichMessageText(_RTelegramMethod[_RUnion[_RMessage, bool]]):
    __returning__ = _RUnion[_RMessage, bool]
    __api_method__ = "editMessageText"

    rich_message: _RDict[str, _RAny]
    business_connection_id: _ROptional[str] = None
    chat_id: _ROptional[_RUnion[int, str]] = None
    message_id: _ROptional[int] = None
    inline_message_id: _ROptional[str] = None


# ───────── مساعدات ─────────
def _resolve_default(bot, value, name):
    """يحل كائنات aiogram Default قبل أي تسلسل JSON (سبب خطأ: Object of type Default is not JSON serializable)."""
    if isinstance(value, _RDefault):
        try:
            return getattr(bot.default, value.name)
        except Exception:
            try:
                return bot.default[value.name]
            except Exception:
                return None
    return value


def _is_html_mode(bot, method):
    pm = _resolve_default(bot, getattr(method, "parse_mode", None), "parse_mode")
    if pm is None:
        return False, False       # (supported, is_html)
    pm_s = str(getattr(pm, "value", pm)).strip().lower()
    if pm_s == "html":
        return True, True
    raise _RichUnsupported(f"parse_mode={pm_s} غير مدعوم في التحويل")


def _text_to_body(bot, method, text):
    if getattr(method, "entities", None):
        raise _RichUnsupported("الرسالة تستخدم entities صريحة")
    _, is_html = _is_html_mode(bot, method)
    return tg_html_to_rich(text) if is_html else plain_to_rich(text)


def _common_send_fields(bot, method):
    fields = {}
    for name in ("business_connection_id", "message_thread_id", "direct_messages_topic_id",
                 "disable_notification", "protect_content", "allow_paid_broadcast",
                 "message_effect_id", "reply_parameters"):
        value = _resolve_default(bot, getattr(method, name, None), name)
        if value is not None and value is not False:
            fields[name] = value
    if "reply_parameters" not in fields:
        legacy = getattr(method, "reply_to_message_id", None)
        if legacy:
            fields["reply_parameters"] = _RReplyParameters(message_id=legacy)
    return fields


def _unsupp_key(method):
    bc = getattr(method, "business_connection_id", None)
    return f"bc:{bc}" if bc else f"chat:{getattr(method, 'chat_id', None)}"


def _scope_of(method):
    return getattr(method, "business_connection_id", None) or "private"


def _breaker_open(scope):
    for key in ("*", scope):
        st = _RICH_BREAKER.get(key)
        if st and st.get("until", 0) > _rtime.time():
            return True
    return False


def _breaker_fail(scope, hard=False):
    key = "*" if hard else scope
    st = _RICH_BREAKER.setdefault(key, {"fail": 0, "until": 0.0})
    st["fail"] += 1
    if hard or st["fail"] >= RICH_BREAKER_THRESHOLD:
        st["until"] = _rtime.time() + RICH_BREAKER_SECONDS
        st["fail"] = 0
        rich_logger.error("RICH معطّل مؤقتًا لمدة %ss (النطاق=%s) بعد رفض متكرر من الخادم؛ ستُرسل الأزرار بالطريقة الكلاسيكية.",
                          RICH_BREAKER_SECONDS, "الكل" if hard else scope)


def _breaker_ok(scope):
    st = _RICH_BREAKER.get(scope)
    if st:
        st["fail"] = 0


_CHAT_ERRORS = (
    "chat not found", "user is deactivated", "bot was blocked", "bot can't initiate", "forbidden",
    "chat_write_forbidden", "have no rights to send", "peer_id_invalid", "not enough rights",
    "bot was kicked", "chat is deactivated", "group chat was upgraded", "need administrator rights",
    "business connection not found", "business_peer_invalid", "user not found",
)
_EDIT_PASSTHROUGH = (
    "message is not modified", "message to edit not found", "message can't be edited",
    "message_id_invalid", "no text in the message to edit", "message to be edited",
)


def _cache_put(chat_id, message_id, body):
    if chat_id is None or message_id is None:
        return
    key = (str(chat_id), int(message_id))
    _RICH_BODY_CACHE[key] = body
    _RICH_BODY_CACHE.move_to_end(key)
    while len(_RICH_BODY_CACHE) > RICH_CACHE_LIMIT:
        _RICH_BODY_CACHE.popitem(last=False)


def _cache_get(chat_id, message_id):
    if chat_id is None or message_id is None:
        return None
    return _RICH_BODY_CACHE.get((str(chat_id), int(message_id)))


# رسائل تبقى بالأزرار العادية دائمًا (لأن ألوان أزرارها تتغير مع الاستخدام): لعبة XO
RICH_CLASSIC_PREFIXES = ("xo:", "xo_new:", "xo_close:")


def _is_classic_only(markup):
    for row in getattr(markup, "inline_keyboard", None) or []:
        for btn in row:
            cb = getattr(btn, "callback_data", None)
            if cb and cb.startswith(RICH_CLASSIC_PREFIXES):
                return True
    return False


def _has_rows(markup):
    return bool(markup is not None and getattr(markup, "inline_keyboard", None))


# ───────── التخطيط: يحوّل طلب كلاسيكي إلى طلب Rich (أو None إن لم يلزم) ─────────
def _rich_plan(bot, method):
    kind = type(method).__name__
    markup = getattr(method, "reply_markup", None)
    if _has_rows(markup) and _is_classic_only(markup):
        return None            # XO وغيرها: تبقى كلاسيكية لتعمل ألوان الأزرار
    if kind == "SendMessage" and _has_rows(markup) and isinstance(method.text, str):
        body = _text_to_body(bot, method, method.text)
        full = body + markup_to_rich_html(markup)
        rm = SendRichMessage(chat_id=method.chat_id, rich_message={"html": full}, **_common_send_fields(bot, method))
        return rm, {"body": body, "chat_id": method.chat_id, "message_id": None, "scope": _scope_of(method), "send": True}
    if kind == "EditMessageText" and _has_rows(markup) and isinstance(method.text, str):
        body = _text_to_body(bot, method, method.text)
        full = body + markup_to_rich_html(markup)
        rm = EditRichMessageText(
            rich_message={"html": full},
            business_connection_id=getattr(method, "business_connection_id", None),
            chat_id=getattr(method, "chat_id", None),
            message_id=getattr(method, "message_id", None),
            inline_message_id=getattr(method, "inline_message_id", None),
        )
        return rm, {"body": body, "chat_id": method.chat_id, "message_id": method.message_id, "scope": _scope_of(method), "send": False}
    if kind == "EditMessageReplyMarkup":
        body = _cache_get(getattr(method, "chat_id", None), getattr(method, "message_id", None))
        if body is None:
            return None            # رسالة كلاسيكية أو غير معروفة للذاكرة المؤقتة → تعديل كلاسيكي كما كان
        full = body + (markup_to_rich_html(markup) if _has_rows(markup) else "")
        if not full.strip():
            return None
        rm = EditRichMessageText(
            rich_message={"html": full},
            business_connection_id=getattr(method, "business_connection_id", None),
            chat_id=method.chat_id, message_id=method.message_id,
            inline_message_id=getattr(method, "inline_message_id", None),
        )
        return rm, {"body": body, "chat_id": method.chat_id, "message_id": method.message_id, "scope": _scope_of(method), "send": False}
    if RICH_MEDIA and kind in ("SendPhoto", "SendVideo", "SendAudio") and _has_rows(markup):
        src_name, tag, mtype = {
            "SendPhoto": ("photo", "img", "photo"),
            "SendVideo": ("video", "video", "video"),
            "SendAudio": ("audio", "audio", "audio"),
        }[kind]
        src = getattr(method, src_name, None)
        if not isinstance(src, str):
            raise _RichUnsupported("ميديا مرفوعة كملف (ليست file_id/URL) → تبقى رسالة ميديا أصلية")
        caption = getattr(method, "caption", None)
        body = _text_to_body(bot, _CaptionView(method), caption) if caption else ""
        node = f'<img src="tg://photo?id=m1"/>' if tag == "img" else f'<{tag} src="tg://{mtype}?id=m1"></{tag}>'
        full = node + body + markup_to_rich_html(markup)
        payload = {"html": full, "media": [{"id": "m1", "media": {"type": mtype, "media": src}}]}
        rm = SendRichMessage(chat_id=method.chat_id, rich_message=payload, **_common_send_fields(bot, method))
        return rm, {"body": node + body, "chat_id": method.chat_id, "message_id": None, "scope": _scope_of(method), "send": True}
    return None


class _CaptionView:
    """يعرض caption/parse_mode كأنها text/parse_mode ليُعاد استخدام نفس المحوّل."""
    def __init__(self, method):
        self.parse_mode = getattr(method, "parse_mode", None)
        self.entities = getattr(method, "caption_entities", None)


# ───────── الـMiddleware المركزي ─────────
async def rich_buttons_middleware(make_request, bot, method):
    if not _RICH_RT["enabled"]:
        return await make_request(bot, method)
    kind = type(method).__name__
    try:
        plan = _rich_plan(bot, method)
    except _RichUnsupported as exc:
        _rstat("unsupported")
        rich_logger.warning("RICH تخطّي %s → كلاسيكي (الوظائف محفوظة). السبب: %s", kind, exc)
        _rich_notify(bot, f"تخطّي {kind}", exc)
        plan = None
    except Exception:
        rich_logger.exception("RICH فشل التخطيط لـ%s → كلاسيكي", kind)
        import traceback as _tb
        _rich_notify(bot, f"فشل التخطيط {kind}", _tb.format_exc().strip().splitlines()[-1])
        plan = None
    if plan is None:
        return await make_request(bot, method)

    rich_method, meta = plan
    scope = meta["scope"]
    ukey = _unsupp_key(method)
    if _RICH_UNSUPPORTED.get(ukey, 0) > _rtime.time():
        _rstat("skipped")
        return await make_request(bot, method)      # حساب غير مميز: أزرار عادية بصمت
    if _breaker_open(scope):
        _rstat("skipped")
        return await make_request(bot, method)
    try:
        json.dumps(rich_method.rich_message, ensure_ascii=False)
    except TypeError:
        rich_logger.exception("RICH payload غير قابل للتسلسل JSON → كلاسيكي")
        return await make_request(bot, method)

    try:
        result = await make_request(bot, rich_method)
    except _RRetryAfter:
        raise                                   # لم تُرسل بعد؛ المستدعي يتعامل مع FloodWait
    except (_RNetworkError, _RServerError) as exc:
        rich_logger.warning("RICH %s: انقطاع/خطأ خادم (%s) — نتيجة التسليم غير معروفة، لا إعادة إرسال تلقائية لتفادي التكرار.", kind, exc)
        raise
    except _RForbidden as exc:
        _rstat("chat_errors")
        rich_logger.warning("RICH %s: خطأ خاص بالمحادثة/الصلاحيات (ليس فشل Rich) chat=%s: %s", kind, meta["chat_id"], exc)
        raise
    except _RNotFound as exc:
        rich_logger.error("RICH الطريقة غير موجودة على الخادم (404) → تعطيل Rich مؤقتًا. التفاصيل: %s", exc)
        _rich_notify(bot, "الطريقة غير موجودة (404)", exc)
        _breaker_fail(scope, hard=True)
        _rstat("fallback")
        return await make_request(bot, method)
    except _RBadRequest as exc:
        reason = str(exc).lower()
        if "rich_message_unsupported" in reason:
            # الحساب/المحادثة لا تدعم الرسائل الغنية (مثلًا صاحب الحساب غير مشترك Premium) → سلوك طبيعي وليس خطأ
            _RICH_UNSUPPORTED[ukey] = _rtime.time() + RICH_UNSUPPORTED_SECONDS
            _rstat("account_unsupported")
            rich_logger.info("RICH غير مدعوم لهذا الحساب/المحادثة (%s) → أزرار عادية لمدة %s ثانية بدون إزعاج.", ukey, RICH_UNSUPPORTED_SECONDS)
            return await make_request(bot, method)
        if any(p in reason for p in _CHAT_ERRORS):
            _rstat("chat_errors")
            rich_logger.warning("RICH %s: chat/access error (منفصل عن Rich) chat=%s: %s", kind, meta["chat_id"], exc)
            raise
        if not meta["send"] and any(p in reason for p in _EDIT_PASSTHROUGH):
            _rstat("passthrough")
            raise                               # سلوك التعديل القديم يعتمد على نفس الاستثناء
        _rstat("fallback")
        _breaker_fail(scope)
        rich_logger.error("RICH رُفضت من الخادم → fallback كلاسيكي (لن تظهر Rich). method=%s chat=%s scope=%s السبب: %s | html[:300]=%r",
                          kind, meta["chat_id"], scope, exc, rich_method.rich_message.get("html", "")[:300])
        _rich_notify(bot, f"رُفضت {kind}", exc, rich_method.rich_message.get("html", ""))
        return await make_request(bot, method)
    except _RAPIError as exc:
        rich_logger.warning("RICH %s: خطأ Telegram غير مصنّف: %s", kind, exc)
        raise
    # نجاح
    _breaker_ok(scope)
    _rstat("ok")
    if not _RICH_FIRST_OK["logged"]:
        _RICH_FIRST_OK["logged"] = True
        rich_logger.info("RICH ✔ أول رسالة Rich قُبلت من الخادم (method=%s).", kind)
    try:
        if meta["send"]:
            chat = getattr(result, "chat", None)
            _cache_put(getattr(chat, "id", meta["chat_id"]), getattr(result, "message_id", None), meta["body"])
        else:
            _cache_put(meta["chat_id"], meta["message_id"], meta["body"])
    except Exception:
        rich_logger.debug("RICH cache put failed", exc_info=True)
    return result


async def rich_startup_probe(bot):
    """RICH_PROBE=1: يجرّب أجزاء الصيغة كل على حدة، يطبع النتيجة في الـConsole ويرسل ملخصًا للمالك، ويضبط <br> تلقائيًا."""
    if not RICH_PROBE:
        return
    row = lambda inner, st="success": ('<tg-button-row><tg-button type="callback_data" data="rich_probe_ok" style="%s">%s</tg-button></tg-button-row>' % (st, inner))
    tests = [
        ("base", "<p>اختبار أساسي</p>" + row("زر")),
        ("br", "<p>سطر1<br>سطر2</p>" + row("زر")),
        ("quote", "<blockquote>اقتباس</blockquote>" + row("زر")),
        ("quote_br", "<blockquote><b>أ<br><br>ب</b></blockquote>" + row("زر")),
        ("emoji_in_text", '<p><tg-emoji emoji-id="5985478698722136468">👋</tg-emoji> نص</p>' + row("زر")),
        ("emoji_in_button", "<p>إيموجي داخل زر</p>" + row('<tg-emoji emoji-id="5445128296276718145">⭐</tg-emoji> زر', "primary")),
        ("emoji_btn_bullet(للمقارنة)", "<p>بديل • داخل زر</p>" + row('<tg-emoji emoji-id="5445128296276718145">•</tg-emoji> زر', "primary")),
    ]
    results = {}
    for name, body in tests:
        try:
            await bot(SendRichMessage(chat_id=OWNER_ID, rich_message={"html": body}))
            results[name] = (True, "")
            rich_logger.info("RICH PROBE ✔ %s", name)
        except Exception as exc:
            results[name] = (False, str(exc))
            rich_logger.error("RICH PROBE ✘ %s: %s", name, exc)
    try:
        real_kb = public_kb(OWNER_ID)
        rows_html = markup_to_rich_html(real_kb)
        welcome_html = tg_html_to_rich(BOT_MESSAGE_DEFAULTS.get("welcome", "") or "نص")
        for name, body in (("real_kb", "<p>أزرار المشروع الحقيقية</p>" + rows_html), ("real_text", welcome_html + rows_html)):
            try:
                await bot(SendRichMessage(chat_id=OWNER_ID, rich_message={"html": body}))
                results[name] = (True, "")
                rich_logger.info("RICH PROBE ✔ %s", name)
            except Exception as exc:
                results[name] = (False, str(exc))
                rich_logger.error("RICH PROBE ✘ %s: %s", name, exc)
        if not results.get("real_kb", (True,))[0]:
            for row in real_kb.inline_keyboard:
                for b in row:
                    one = "<p>اختبار زر واحد</p><tg-button-row>" + rich_button_html(b) + "</tg-button-row>"
                    try:
                        await bot(SendRichMessage(chat_id=OWNER_ID, rich_message={"html": one}))
                    except Exception as exc:
                        results[f"زر مرفوض: {b.text} (icon={getattr(b, 'icon_custom_emoji_id', None)})"] = (False, str(exc))
                        rich_logger.error("RICH PROBE زر مرفوض %r icon=%s: %s", b.text, getattr(b, "icon_custom_emoji_id", None), exc)
    except Exception as exc:
        rich_logger.exception("RICH PROBE: فشل فحص أزرار المشروع الحقيقية")
        results["real_kb_probe"] = (False, str(exc))
    _RICH_CAPS["br"] = results["br"][0] and results["quote_br"][0]
    rich_logger.info("RICH استخدام <br> = %s", _RICH_CAPS["br"])
    lines = ["نتيجة فحص Rich:"] + [("✔ " if ok else "✘ ") + n + ("" if ok else " — " + html.escape(err)) for n, (ok, err) in results.items()]
    lines.append("وضع الأسطر: " + ("<br>" if _RICH_CAPS["br"] else "فقرات <p> (تلقائي)"))
    try:
        await bot.send_message(OWNER_ID, "\n".join(lines))
    except Exception:
        rich_logger.debug("تعذر إرسال ملخص الفحص", exc_info=True)


@router.message(Command("richstats"))
async def richstats_cmd(message: Message):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    now = _rtime.time()
    br = ", ".join(f"{k}: {'مفتوحة' if v.get('until', 0) > now else 'سليمة'}" for k, v in _RICH_BREAKER.items()) or "لا شيء"
    await message.answer(
        "إحصاءات Rich منذ التشغيل:\n"
        f"✔ رسائل Rich ناجحة: {_RICH_STATS['ok']}\n"
        f"↩ رجعت للكلاسيكي بعد رفض: {_RICH_STATS['fallback']}\n"
        f"⏭ تخطّي بسبب قاطع الدائرة: {_RICH_STATS['skipped']}\n"
        f"⚠ بنية غير مدعومة: {_RICH_STATS['unsupported']}\n"
        f"👤 حسابات/محادثات لا تدعم Rich (أزرار عادية): {_RICH_STATS['account_unsupported']}\n"
        f"⛔ أخطاء محادثة: {_RICH_STATS['chat_errors']}\n"
        f"القاطع: {br}\nوضع الأسطر: {'<br>' if _RICH_CAPS['br'] else '<p>'}",
        parse_mode=None)


# ═══════════════════════════════════════════════════════════════════════════
# محرر الأزرار الموحّد (ردود تلقائية / ترحيب / إذاعة) — نظام واحد لكل الأقسام
# يدعم: إضافة، تعديل (اسم/قيمة/لون/إيموجي مميز)، حذف، ترتيب، عدد الأزرار بالصف، معاينة، حفظ.
# التخزين متوافق مع الموجود: reply_buttons كما هي، وأزرار الترحيب JSON في settings.welcome_buttons،
# وترتيب صفوف الردود في bot_messages (مفتاح __rich_rows__) دون أي تغيير في بنية قاعدة البيانات.
# ═══════════════════════════════════════════════════════════════════════════
import secrets as _secrets

BTED_TYPES = {"text": "نص", "url": "رابط", "copy": "نسخ"}
BTED_ROWMAP_KEY = "__rich_rows__"
BTED_MAX_ITEMS = 24
_ROW_MAP = {}          # reply_buttons.id -> رقم الصف


class BtnEdSG(StatesGroup):
    label = State()
    value = State()
    field = State()


class BcSG(StatesGroup):
    stage = State()


async def load_row_map():
    try:
        raw = await get_bot_message(BTED_ROWMAP_KEY)
        data = json.loads(raw or "{}")
        _ROW_MAP.clear()
        _ROW_MAP.update({int(k): int(v) for k, v in data.items()})
    except Exception:
        logger.warning("تعذر تحميل ترتيب صفوف أزرار الردود؛ سيُستخدم الترتيب الافتراضي.", exc_info=True)


async def _save_row_map():
    await set_bot_message(BTED_ROWMAP_KEY, json.dumps({str(k): v for k, v in _ROW_MAP.items()}))


def _group_rows(built, row_ids):
    """يجمّع الأزرار المتتالية ذات رقم الصف نفسه؛ وإلا الترتيب الافتراضي القديم (زرّان في الصف)."""
    if built and len(row_ids) == len(built) and all(isinstance(r, int) for r in row_ids):
        rows, last = [], None
        for btn, r in zip(built, row_ids):
            if rows and r == last:
                rows[-1].append(btn)
            else:
                rows.append([btn])
                last = r
        return rows
    return [built[i:i + 2] for i in range(0, len(built), 2)]


def _rows_for_reply(buttons, built):
    try:
        ids = [_ROW_MAP.get(int(b["id"])) for b in buttons]
    except Exception:
        ids = []
    return _group_rows(built, ids)


def _rows_for_welcome(buttons, built):
    return _group_rows(built, [b.get("row") for b in buttons])


# ───────── عناصر مشتركة ─────────
def _bted_relayout(items, size):
    for i, it in enumerate(items):
        it["row"] = i // size


def _bted_next_row(items, size):
    if not items:
        return 0
    last = items[-1]["row"]
    return last if sum(1 for it in items if it["row"] == last) < size else last + 1


def _bted_norm(it):
    return {
        "id": it.get("id"),
        "label": it.get("label") or "زر",
        "type": it.get("type") if it.get("type") in BTED_TYPES else "text",
        "color": it.get("color") if it.get("color") in BTN_STYLE_MAP else "primary",
        "icon_custom_emoji_id": it.get("icon_custom_emoji_id") or "",
        "value": it.get("value") or "",
        "row": it.get("row"),
    }


def _bted_fix_rows(items, size_hint=2):
    if not items:
        return items
    if not all(isinstance(it.get("row"), int) for it in items):
        _bted_relayout(items, size_hint)
    return items


def _bted_parse_label(message):
    """اسم الزر + معرّف الإيموجي المميز (من entities أو الصيغة: اسم | 123456…)."""
    text = message.text or ""
    emoji_id = ""
    ents = [e for e in (message.entities or []) if e.type == "custom_emoji" and e.custom_emoji_id]
    if ents:
        emoji_id = ents[0].custom_emoji_id
        raw = text.encode("utf-16-le")
        for e in sorted(ents, key=lambda x: x.offset, reverse=True):
            raw = raw[:e.offset * 2] + raw[(e.offset + e.length) * 2:]
        text = raw.decode("utf-16-le")
    m = re.search(r"\|\s*(\d{6,})\s*$", text)
    if m:
        emoji_id = emoji_id or m.group(1)
        text = text[:m.start()]
    return re.sub(r"[ \t]+", " ", text).strip(), emoji_id


def _bted_validate(btype, value):
    value = (value or "").strip()
    if btype == "url":
        value = _clean_button_url(value)
        if not _valid_button_url(value) or not value.startswith(("http://", "https://")):
            return None, "الرابط غير صالح. أرسل رابطاً يبدأ بـ http:// أو https:// بدون مسافات."
    if not value:
        return None, "اكتب قيمة صحيحة."
    if btype == "copy" and len(value) > 256:
        return None, "نص النسخ لا يزيد عن 256 حرفًا."
    if btype == "text" and len(value) > 3500:
        return None, "النص طويل جدًا (الحد 3500 حرف)."
    return value, None


def _bted_preview_markup(items):
    rows, last = [], None
    for it in items:
        base = {"text": it["label"], "style": BTN_STYLE_MAP.get(it["color"], "primary")}
        if it.get("icon_custom_emoji_id"):
            base["icon_custom_emoji_id"] = it["icon_custom_emoji_id"]
        if it["type"] == "url":
            # تنظيف الرابط يحافظ على صلاحيته في المعاينة والإرسال الكلاسيكي أيضاً.
            clean_url = _clean_button_url(it["value"])
            if not _valid_button_url(clean_url) or not clean_url.startswith(("http://", "https://")):
                raise ValueError(f"رابط الزر غير صالح: {it.get('label', 'زر')}")
            base["url"] = clean_url
        elif it["type"] == "copy":
            base["copy_text"] = CopyTextButton(text=it["value"])
        else:
            base["callback_data"] = "bted_pv"
        btn = InlineKeyboardButton(**base)
        if rows and it["row"] == last:
            rows[-1].append(btn)
        else:
            rows.append([btn])
            last = it["row"]
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


# ───────── تحميل / حفظ حسب القسم ─────────
async def _bted_load(call, state, kind, ref):
    uid = call.from_user.id
    data = await state.get_data()
    ctx = {"kind": kind, "ref": ref, "size": 2, "items": [], "text": "", "title": ""}
    if kind == "reply":
        owner = await settings_owner(uid)
        conn = await db()
        try:
            row = await fetchone(conn, "SELECT id, trigger, response FROM replies WHERE id=? AND owner_id=?", (int(ref), owner))
            if not row:
                return None
            btns = await conn.execute_fetchall(
                "SELECT id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value FROM reply_buttons WHERE reply_id=? ORDER BY position, id",
                (int(ref),))
        finally:
            await conn.close()
        ctx["text"], ctx["title"] = row["response"] or "", f"رد #{row['id']}"
        ctx["items"] = [_bted_norm({"id": b["id"], "label": b["label"], "type": b["btn_type"], "color": b["btn_color"],
                                    "icon_custom_emoji_id": b["icon_custom_emoji_id"], "value": b["btn_value"],
                                    "row": _ROW_MAP.get(b["id"])}) for b in btns]
    elif kind == "replydraft":
        ctx["text"], ctx["title"] = data.get("response") or "", "رد جديد"
        ctx["items"] = [_bted_norm(b) for b in (data.get("buttons") or [])]
    elif kind in ("welcome", "welcomedraft"):
        owner = await settings_owner(uid)
        ctx["text"] = (await get_account_setting(owner, "welcome")) or ""
        ctx["title"] = "رسالة الترحيب"
        if kind == "welcome":
            try:
                raw = json.loads(await get_account_setting(owner, "welcome_buttons") or "[]")
            except Exception:
                raw = []
        else:
            raw = data.get("welcome_buttons") or []
        ctx["items"] = [_bted_norm(b) for b in raw]
    elif kind == "paidgate":
        cfg = await _paid_gate_load()
        ctx["text"], ctx["title"] = cfg["text"], "رسالة غير المشتركين"
        ctx["items"] = [_bted_norm(b) for b in cfg["buttons"]]
    elif kind == "bc":
        bc = data.get("bc") or {}
        ctx["text"], ctx["title"] = bc.get("text") or "", "رسالة الإذاعة"
        ctx["items"] = [_bted_norm(b) for b in (data.get("bc_buttons") or [])]
    else:
        return None
    if ctx["items"] and all(isinstance(it["row"], int) for it in ctx["items"]):
        counts = {}
        for it in ctx["items"]:
            counts[it["row"]] = counts.get(it["row"], 0) + 1
        ctx["size"] = max(1, min(4, max(counts.values())))
    _bted_fix_rows(ctx["items"], ctx["size"])
    return ctx


async def _bted_commit(call, state, ctx):
    kind, items = ctx["kind"], ctx["items"]
    if kind == "reply":
        rid, owner = int(ctx["ref"]), await settings_owner(call.from_user.id)
        removed = []
        conn = await db()
        try:
            row = await fetchone(conn, "SELECT id FROM replies WHERE id=? AND owner_id=?", (rid, owner))
            if not row:
                return False
            old = {r["id"] for r in await conn.execute_fetchall("SELECT id FROM reply_buttons WHERE reply_id=?", (rid,))}
            keep = set()
            for pos, it in enumerate(items):
                vals = (it["label"], it["type"], it["color"], it["icon_custom_emoji_id"], it["value"], pos)
                if it.get("id") in old:
                    await conn.execute(
                        "UPDATE reply_buttons SET label=?, btn_type=?, btn_color=?, icon_custom_emoji_id=?, btn_value=?, position=? WHERE id=?",
                        vals + (it["id"],))
                    keep.add(it["id"])
                else:
                    cur = await conn.execute(
                        "INSERT INTO reply_buttons(reply_id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value, position) VALUES(?,?,?,?,?,?,?)",
                        (rid,) + vals)
                    it["id"] = cur.lastrowid
                    keep.add(it["id"])
            for oid in old - keep:
                await conn.execute("DELETE FROM reply_buttons WHERE id=?", (oid,))
                removed.append(oid)
            await conn.commit()
        finally:
            await conn.close()
        for oid in removed:
            _ROW_MAP.pop(oid, None)
        for it in items:
            _ROW_MAP[int(it["id"])] = int(it["row"])
        await _save_row_map()
        return True
    out = [{k: v for k, v in it.items() if k != "id"} for it in items]
    if kind == "paidgate":
        if call.from_user.id != OWNER_ID:
            return False
        cfg = await _paid_gate_load()
        cfg["buttons"] = out
        await _paid_gate_save(cfg)
    elif kind == "replydraft":
        await state.update_data(buttons=[{**b, "icon_custom_emoji_id": b["icon_custom_emoji_id"]} for b in out])
    elif kind == "welcome":
        await set_account_setting(await settings_owner(call.from_user.id), "welcome_buttons", json.dumps(out, ensure_ascii=False))
    elif kind == "welcomedraft":
        await state.update_data(welcome_buttons=out)
    elif kind == "bc":
        await state.update_data(bc_buttons=out)
    return True


# ───────── شاشات ─────────
def _bted_menu_text(ctx):
    lines = []
    for i, it in enumerate(ctx["items"], 1):
        lines.append(f"{i}. {html.escape(it['label'])} — {BTED_TYPES.get(it['type'], it['type'])} — "
                     f"{STYLE_LABEL.get(it['color'], it['color'])} — صف {it['row'] + 1}")
    body = "\n".join(lines) if lines else "لا توجد أزرار بعد."
    return f"<b>إدارة الأزرار — {html.escape(ctx['title'])}</b>\n\n{body}\n\nعدد الأزرار في الصف: <b>{ctx['size']}</b>"


def _bted_menu_kb(ctx):
    rows = [[InlineKeyboardButton(text="إضافة زر", callback_data="bted_add", style="primary", icon_custom_emoji_id="6039450962865688331")]]
    if ctx["items"]:
        rows.append([InlineKeyboardButton(text="تعديل زر", callback_data="bted_sel_edit", style="primary"),
                     InlineKeyboardButton(text="حذف زر", callback_data="bted_sel_del", style="danger", icon_custom_emoji_id="6039522349517115015")])
    rows.append([InlineKeyboardButton(text=f"عدد الأزرار بالصف: {ctx['size']}", callback_data="bted_size_menu", style="primary")])
    rows.append([InlineKeyboardButton(text="معاينة", callback_data="bted_prev", style="primary", icon_custom_emoji_id="6037397706505195857"),
                 InlineKeyboardButton(text="حفظ", callback_data="bted_save", style="success", icon_custom_emoji_id="5963087934696459905")])
    rows.append([InlineKeyboardButton(text="إلغاء", callback_data="bted_cancel", style="danger", icon_custom_emoji_id="5447647474984449520")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _bted_get(state):
    return (await state.get_data()).get("bted")


async def _bted_show(call_or_msg, state, ctx, edit=True):
    await state.update_data(bted=ctx)
    await state.set_state(None)
    text, kb = _bted_menu_text(ctx), _bted_menu_kb(ctx)
    if edit and hasattr(call_or_msg, "message"):
        await edit_or_replace(call_or_msg, text, kb)
    else:
        target = call_or_msg.message if hasattr(call_or_msg, "message") else call_or_msg
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


async def _bted_open(call, state, kind, ref):
    if not await is_admin(call.from_user.id):
        return
    if kind == "paidgate" and call.from_user.id != OWNER_ID:
        return
    ctx = await _bted_load(call, state, kind, ref)
    if ctx is None:
        await call.answer("غير موجود أو انتهت الجلسة.", show_alert=True)
        return
    await _bted_show(call, state, ctx)
    await call.answer()


@router.callback_query(F.data.startswith("bted_open_"))
async def bted_open_cb(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")          # bted _ open _ kind _ ref
    if len(parts) < 4:
        await call.answer()
        return
    await _bted_open(call, state, parts[2], parts[3])


@router.callback_query(F.data == "bted_menu")
async def bted_menu_cb(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    await _bted_show(call, state, ctx)
    await call.answer()


@router.callback_query(F.data == "bted_pv")
async def bted_pv_cb(call: CallbackQuery):
    await call.answer("هذه معاينة فقط — سيعمل الزر بعد الحفظ والإرسال.", show_alert=False)


# --- إضافة زر ---
@router.callback_query(F.data == "bted_add")
async def bted_add_cb(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    if len(ctx["items"]) >= BTED_MAX_ITEMS:
        await call.answer(f"الحد الأقصى {BTED_MAX_ITEMS} زرًا.", show_alert=True)
        return
    await state.set_state(BtnEdSG.label)
    await edit_or_replace(call, "<b>إضافة زر</b>\n\nأرسل اسم الزر.\nلإضافة إيموجي مميز اكتبه مع الاسم في نفس الرسالة.",
                          cancel_kb("bted_menu"))
    await call.answer()


@router.message(BtnEdSG.label)
async def bted_label_msg(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    label, emoji_id = _bted_parse_label(message)
    if not label:
        await message.answer("اكتب اسم الزر بجانب الإيموجي المميز.")
        return
    await state.update_data(bted_new={"label": label, "icon_custom_emoji_id": emoji_id})
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="زر نص", callback_data="bted_t_text", style="primary", icon_custom_emoji_id="5445128296276718145")],
        [InlineKeyboardButton(text="زر رابط", callback_data="bted_t_url", style="primary", icon_custom_emoji_id="5778455936410588193")],
        [InlineKeyboardButton(text="زر نسخ", callback_data="bted_t_copy", style="primary", icon_custom_emoji_id="5467397594332275071")],
        [InlineKeyboardButton(text="إلغاء", callback_data="bted_menu", style="danger", icon_custom_emoji_id="5447647474984449520")],
    ])
    await message.answer(f"<b>اسم الزر:</b> {html.escape(label)}\n\nاختر النوع:", reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("bted_t_"))
async def bted_type_cb(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    btype = call.data[len("bted_t_"):]
    data = await state.get_data()
    if btype not in BTED_TYPES or not data.get("bted_new"):
        await call.answer("ابدأ إضافة الزر من جديد.", show_alert=True)
        return
    new = dict(data["bted_new"], type=btype)
    await state.update_data(bted_new=new)
    await state.set_state(BtnEdSG.value)
    hint = {"url": "أرسل الرابط (يبدأ بـ http:// أو https://).",
            "copy": "أرسل النص الذي سيُنسخ عند الضغط.",
            "text": "أرسل النص الذي سيُرسل عند الضغط على الزر."}[btype]
    await edit_or_replace(call, f"<b>النوع:</b> {BTED_TYPES[btype]}\n\n{hint}", cancel_kb("bted_menu"))
    await call.answer()


@router.message(BtnEdSG.value)
async def bted_value_msg(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    new = data.get("bted_new")
    if not new:
        await message.answer("ابدأ إضافة الزر من جديد.")
        return
    value, err = _bted_validate(new.get("type"), message.html_text if new.get("type") == "text" else message.text)
    if err:
        await message.answer(err)
        return
    await state.update_data(bted_new=dict(new, value=value))
    await state.set_state(None)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="أحمر", callback_data="bted_c_danger", style="danger", icon_custom_emoji_id="5936035511951958098")],
        [InlineKeyboardButton(text="أخضر", callback_data="bted_c_success", style="success", icon_custom_emoji_id="5935967441015282912")],
        [InlineKeyboardButton(text="أزرق", callback_data="bted_c_primary", style="primary", icon_custom_emoji_id="5936274131744988204")],
    ])
    await message.answer("<b>اختر لون الزر:</b>", reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("bted_c_"))
async def bted_color_cb(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    color = call.data[len("bted_c_"):]
    data = await state.get_data()
    ctx, new = data.get("bted"), data.get("bted_new")
    if color not in BTN_STYLE_MAP or not ctx or not new or "value" not in new:
        await call.answer("ابدأ إضافة الزر من جديد.", show_alert=True)
        return
    item = _bted_norm(dict(new, color=color, row=_bted_next_row(ctx["items"], ctx["size"])))
    ctx["items"].append(item)
    await state.update_data(bted_new=None)
    await _bted_show(call, state, ctx)
    await call.answer("تمت إضافة الزر.")


# --- تعديل / حذف ---
def _bted_pick_kb(ctx, prefix, back="bted_menu"):
    rows = [[InlineKeyboardButton(text=f"{i + 1}. {it['label']}"[:60], callback_data=f"{prefix}{i}",
                                  style=BTN_STYLE_MAP.get(it["color"], "primary"))] for i, it in enumerate(ctx["items"])]
    rows.append([InlineKeyboardButton(text="رجوع", callback_data=back, style="danger", icon_custom_emoji_id="5445365692004071819")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "bted_sel_edit")
async def bted_sel_edit(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx or not ctx["items"]:
        await call.answer("لا توجد أزرار.", show_alert=True)
        return
    await edit_or_replace(call, "<b>اختر الزر المراد تعديله:</b>", _bted_pick_kb(ctx, "bted_pick_"))
    await call.answer()


@router.callback_query(F.data == "bted_sel_del")
async def bted_sel_del(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx or not ctx["items"]:
        await call.answer("لا توجد أزرار.", show_alert=True)
        return
    await edit_or_replace(call, "<b>اختر الزر المراد حذفه:</b>", _bted_pick_kb(ctx, "bted_del_"))
    await call.answer()


def _bted_item_kb(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="الاسم", callback_data=f"bted_f_label_{i}", style="primary"),
         InlineKeyboardButton(text="القيمة", callback_data=f"bted_f_value_{i}", style="primary")],
        [InlineKeyboardButton(text="أحمر", callback_data=f"bted_ic_danger_{i}", style="danger"),
         InlineKeyboardButton(text="أخضر", callback_data=f"bted_ic_success_{i}", style="success"),
         InlineKeyboardButton(text="أزرق", callback_data=f"bted_ic_primary_{i}", style="primary")],
        [InlineKeyboardButton(text="تغيير الإيموجي المميز", callback_data=f"bted_f_emoji_{i}", style="primary"),
         InlineKeyboardButton(text="إزالة الإيموجي", callback_data=f"bted_emx_{i}", style="danger")],
        [InlineKeyboardButton(text="▲ للأعلى", callback_data=f"bted_up_{i}", style="primary"),
         InlineKeyboardButton(text="▼ للأسفل", callback_data=f"bted_dn_{i}", style="primary")],
        [InlineKeyboardButton(text="حذف الزر", callback_data=f"bted_del_{i}", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="رجوع", callback_data="bted_menu", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])


async def _bted_item_screen(call, ctx, i):
    it = ctx["items"][i]
    text = (f"<b>تعديل الزر {i + 1}</b>\n\nالاسم: {html.escape(it['label'])}\nالنوع: {BTED_TYPES.get(it['type'])}\n"
            f"القيمة: <code>{html.escape(it['value'][:200])}</code>\nاللون: {STYLE_LABEL.get(it['color'], it['color'])}\n"
            f"إيموجي مميز: {'نعم' if it['icon_custom_emoji_id'] else 'لا'}\nالصف: {it['row'] + 1}")
    await edit_or_replace(call, text, _bted_item_kb(i))


async def _bted_idx(call, state, prefix_len_parts=1):
    ctx = await _bted_get(state)
    try:
        i = int(call.data.rsplit("_", 1)[-1])
    except ValueError:
        return None, None
    if not ctx or i < 0 or i >= len(ctx["items"]):
        await call.answer("الزر غير موجود.", show_alert=True)
        return None, None
    return ctx, i


@router.callback_query(F.data.startswith("bted_pick_"))
async def bted_pick(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    await _bted_item_screen(call, ctx, i)
    await call.answer()


@router.callback_query(F.data.startswith("bted_ic_"))
async def bted_item_color(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    color = call.data.split("_")[2]
    if color not in BTN_STYLE_MAP:
        await call.answer()
        return
    ctx["items"][i]["color"] = color
    await state.update_data(bted=ctx)
    await _bted_item_screen(call, ctx, i)
    await call.answer("تم تغيير اللون.")


@router.callback_query(F.data.startswith("bted_emx_"))
async def bted_emoji_remove(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    ctx["items"][i]["icon_custom_emoji_id"] = ""
    await state.update_data(bted=ctx)
    await _bted_item_screen(call, ctx, i)
    await call.answer("تمت إزالة الإيموجي.")


@router.callback_query(F.data.startswith("bted_up_") | F.data.startswith("bted_dn_"))
async def bted_move(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    j = i - 1 if call.data.startswith("bted_up_") else i + 1
    items = ctx["items"]
    if j < 0 or j >= len(items):
        await call.answer("لا يمكن التحريك أكثر.")
        return
    items[i], items[j] = items[j], items[i]
    items[i]["row"], items[j]["row"] = items[j]["row"], items[i]["row"]   # المواضع تحتفظ بصفوفها
    await state.update_data(bted=ctx)
    await _bted_item_screen(call, ctx, j)
    await call.answer("تم النقل.")


@router.callback_query(F.data.startswith("bted_del_"))
async def bted_delete(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    ctx["items"].pop(i)
    _bted_fix_rows(ctx["items"], ctx["size"])
    # ضغط الصفوف الفارغة مع الحفاظ على التجميع
    seen, remap = {}, 0
    for it in ctx["items"]:
        if it["row"] not in seen:
            seen[it["row"]] = remap
            remap += 1
        it["row"] = seen[it["row"]]
    await _bted_show(call, state, ctx)
    await call.answer("تم حذف الزر.")


@router.callback_query(F.data.startswith("bted_f_"))
async def bted_field_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx, i = await _bted_idx(call, state)
    if ctx is None:
        return
    field = call.data.split("_")[2]
    if field not in ("label", "value", "emoji"):
        await call.answer()
        return
    await state.update_data(bted_field={"field": field, "i": i})
    await state.set_state(BtnEdSG.field)
    hint = {"label": "أرسل الاسم الجديد للزر (يمكنك إضافة إيموجي مميز معه).",
            "value": {"url": "أرسل الرابط الجديد.", "copy": "أرسل نص النسخ الجديد.", "text": "أرسل النص الجديد."}[ctx["items"][i]["type"]],
            "emoji": "أرسل الإيموجي المميز الذي تريده للزر."}[field]
    await edit_or_replace(call, hint, cancel_kb("bted_menu"))
    await call.answer()


@router.message(BtnEdSG.field)
async def bted_field_msg(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    ctx, fld = data.get("bted"), data.get("bted_field")
    if not ctx or not fld or fld["i"] >= len(ctx["items"]):
        await message.answer("انتهت الجلسة.")
        await state.set_state(None)
        return
    it = ctx["items"][fld["i"]]
    if fld["field"] == "label":
        label, emoji_id = _bted_parse_label(message)
        if not label:
            await message.answer("اكتب اسمًا صحيحًا.")
            return
        it["label"] = label
        if emoji_id:
            it["icon_custom_emoji_id"] = emoji_id
    elif fld["field"] == "emoji":
        _, emoji_id = _bted_parse_label(message)
        if not emoji_id:
            await message.answer("أرسل إيموجي مميزًا (Custom Emoji) فقط.")
            return
        it["icon_custom_emoji_id"] = emoji_id
    else:
        value, err = _bted_validate(it["type"], message.html_text if it["type"] == "text" else message.text)
        if err:
            await message.answer(err)
            return
        it["value"] = value
    await state.update_data(bted=ctx, bted_field=None)
    await state.set_state(None)
    await _bted_show(message, state, ctx, edit=False)


# --- عدد الأزرار في الصف ---
@router.callback_query(F.data == "bted_size_menu")
async def bted_size_menu(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(n), callback_data=f"bted_size_{n}", style="primary") for n in (1, 2, 3, 4)],
        [InlineKeyboardButton(text="رجوع", callback_data="bted_menu", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])
    await edit_or_replace(call, "<b>كم زرًا في كل صف؟</b>\nسيُعاد ترتيب كل الأزرار بنفس الترتيب الحالي.", kb)
    await call.answer()


@router.callback_query(F.data.regexp(r"^bted_size_[1-4]$"))
async def bted_size_set(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    ctx["size"] = int(call.data[-1])
    _bted_relayout(ctx["items"], ctx["size"])
    await _bted_show(call, state, ctx)
    await call.answer()


# --- معاينة / حفظ / إلغاء ---
@router.callback_query(F.data == "bted_prev")
async def bted_preview(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    data = await state.get_data()
    ctx = data.get("bted")
    if not ctx:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    markup = _bted_preview_markup(ctx["items"])
    text = ctx["text"] or "(بدون نص)"
    try:
        if ctx["kind"] == "bc":
            await _bc_send_one(call.bot, call.message.chat.id, data.get("bc") or {}, markup, None)
        else:
            await call.message.answer(text, reply_markup=markup, parse_mode="HTML")
    except Exception as exc:
        logger.warning("فشلت المعاينة: %s", exc, exc_info=True)
        await call.answer("تعذر إرسال المعاينة (راجع الـConsole).", show_alert=True)
        return
    await call.answer("هذه هي الرسالة كما ستصل.")


async def _bted_exit(call, state, ctx, saved):
    kind = ctx["kind"]
    note = "<b>تم حفظ الأزرار.</b>" if saved else "<b>تم الإلغاء بدون حفظ.</b>"
    if kind == "reply":
        await state.set_state(None)
        await edit_or_replace(call, note, back_kb(f"redit_{ctx['ref']}"))
    elif kind == "welcome":
        await state.set_state(None)
        await edit_or_replace(call, note, back_kb("welcome_settings"))
    elif kind == "paidgate":
        await state.set_state(None)
        await edit_or_replace(call, note, back_kb("paidgate_menu"))
    elif kind == "replydraft":
        await state.set_state(ReplySG.ask_more)
        await edit_or_replace(call, f"{note}\nعدد الأزرار الآن: <b>{len((await state.get_data()).get('buttons') or [])}</b>\n\nهل تريد إضافة زر آخر؟", reply_more_kb())
    elif kind == "welcomedraft":
        await state.set_state(WelcomeSG.ask_more)
        await edit_or_replace(call, f"{note}\nهل تريد إضافة زر آخر؟", _welcome_more_kb())
    elif kind == "bc":
        await state.set_state(BcSG.stage)
        n = len((await state.get_data()).get("bc_buttons") or [])
        await edit_or_replace(call, f"{note}\n\nعدد أزرار الإذاعة: <b>{n}</b>", _bc_stage_kb(n))


@router.callback_query(F.data == "bted_save")
async def bted_save(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    try:
        ok = await _bted_commit(call, state, ctx)
    except Exception:
        logger.exception("فشل حفظ الأزرار")
        await call.answer("تعذر الحفظ. راجع الـConsole.", show_alert=True)
        return
    if not ok:
        await call.answer("العنصر غير موجود.", show_alert=True)
        return
    await _bted_exit(call, state, ctx, True)
    await call.answer("تم الحفظ.")


@router.callback_query(F.data == "bted_cancel")
async def bted_cancel(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    ctx = await _bted_get(state)
    if not ctx:
        await call.answer()
        return
    await _bted_exit(call, state, ctx, False)
    await call.answer()


def _welcome_more_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إضافة زر آخر", callback_data="welcome_btn_more", style="primary")],
        [InlineKeyboardButton(text="إدارة الأزرار والمعاينة", callback_data="bted_open_welcomedraft_0", style="primary")],
        [InlineKeyboardButton(text="إنهاء الأزرار", callback_data="welcome_btn_done", style="success")],
    ])


# ═══════════════ الإذاعة: إضافة أزرار Rich لكل أنواع الإذاعة الثلاثة ═══════════════
_BC_MEDIA_ORDER = ("photo", "video", "voice", "audio", "document", "animation")
_BC_KIND_TITLE = {"customers": "إذاعة العملاء", "bot": "إذاعة مستخدمي البوت", "channels": "إذاعة القنوات"}


def _bc_extract_media(message, allowed):
    for mtype in _BC_MEDIA_ORDER:
        if mtype not in allowed:
            continue
        obj = getattr(message, mtype, None)
        if obj:
            return {"type": mtype, "file_id": (obj[-1] if mtype == "photo" else obj).file_id}
    return None


def _bc_stage_kb(n):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"إضافة/إدارة الأزرار ({n})", callback_data="bted_open_bc_0", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="معاينة", callback_data="bc_preview", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text="إرسال الآن", callback_data="bc_go", style="success", icon_custom_emoji_id="6206479140040743133")],
        [InlineKeyboardButton(text="إلغاء", callback_data="home", style="danger", icon_custom_emoji_id="5447647474984449520")],
    ])


async def _bc_stage(message, state, kind, text, media, owner=None):
    await state.update_data(bc={"kind": kind, "text": text, "media": media, "owner": owner}, bc_buttons=[], bted=None)
    await state.set_state(BcSG.stage)
    extra = ""
    if kind == "channels":
        names = (await state.get_data()).get("chb_names") or []
        extra = f"\n\n<b>القنوات المحددة ({len(names)}):</b>\n" + "\n".join(html.escape(n) for n in names[:15]) + ("\n..." if len(names) > 15 else "")
    await message.answer(
        f"<b>{_BC_KIND_TITLE[kind]} — تم تجهيز الرسالة.</b>{extra}\n\nيمكنك إضافة أزرار (ألوان/إيموجي مميز/روابط/نسخ/نص) أو معاينتها أو إرسالها الآن.",
        reply_markup=_bc_stage_kb(0), parse_mode="HTML")


async def _bc_send_one(bot, chat_id, bc, markup, connection_id):
    """الإرسال النهائي الموحَّد (نفسه للمعاينة وللمستلمين) — يمر على middleware الـRich تلقائيًا."""
    text = bc.get("text") or ""
    media = bc.get("media")
    kw = {"chat_id": chat_id, "parse_mode": "HTML"}
    if connection_id:
        kw["business_connection_id"] = connection_id
    if markup is not None:
        kw["reply_markup"] = markup
    if media:
        senders = {"photo": bot.send_photo, "video": bot.send_video, "voice": bot.send_voice,
                   "audio": bot.send_audio, "document": bot.send_document, "animation": bot.send_animation}
        return await senders[media["type"]](**{media["type"]: media["file_id"], "caption": text or None}, **kw)
    return await bot.send_message(text=text, **kw)


async def _bc_markup(items):
    """يبني لوحة الإرسال النهائية؛ أزرار «النص» تُحفظ بمفتاح bot_messages ويُرسل رابطها كـcallback bcb_<token>."""
    rows, last = [], None
    for it in items:
        base = {"text": it["label"], "style": BTN_STYLE_MAP.get(it["color"], "primary")}
        if it.get("icon_custom_emoji_id"):
            base["icon_custom_emoji_id"] = it["icon_custom_emoji_id"]
        if it["type"] == "url":
            # إزالة المحارف الخفية من الرابط قبل إنشاء لوحة الإذاعة.
            clean_url = _clean_button_url(it["value"])
            if not _valid_button_url(clean_url) or not clean_url.startswith(("http://", "https://")):
                raise ValueError(f"رابط زر الإذاعة غير صالح: {it.get('label', 'زر')}")
            base["url"] = clean_url
        elif it["type"] == "copy":
            base["copy_text"] = CopyTextButton(text=it["value"])
        else:
            token = _secrets.token_hex(5)
            await set_bot_message(f"__bcb_{token}", it["value"])
            base["callback_data"] = f"bcb_{token}"
        btn = InlineKeyboardButton(**base)
        if rows and it["row"] == last:
            rows[-1].append(btn)
        else:
            rows.append([btn])
            last = it["row"]
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


@router.callback_query(F.data == "bc_preview")
async def bc_preview(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    data = await state.get_data()
    bc = data.get("bc")
    if not bc:
        await call.answer("انتهت الجلسة.", show_alert=True)
        return
    items = [_bted_norm(b) for b in (data.get("bc_buttons") or [])]
    try:
        await _bc_send_one(call.bot, call.message.chat.id, bc, _bted_preview_markup(items), None)
    except Exception as exc:
        logger.warning("فشلت معاينة الإذاعة: %s", exc, exc_info=True)
        await call.answer("تعذر إرسال المعاينة.", show_alert=True)
        return
    await call.answer("هذه هي الرسالة كما ستصل.")


@router.callback_query(F.data == "bc_go")
async def bc_go(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    data = await state.get_data()
    bc = data.get("bc")
    if not bc:
        await call.answer("انتهت الجلسة، ابدأ الإذاعة من جديد.", show_alert=True)
        return
    kind = bc["kind"]
    if kind in ("bot", "channels") and call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    selected = set(data.get("chb_sel") or [])
    if kind == "channels" and not selected:
        await call.answer("لم تُحدَّد أي قناة. ابدأ إذاعة القنوات من جديد.", show_alert=True)
        return
    items = [_bted_norm(b) for b in (data.get("bc_buttons") or [])]
    markup = await _bc_markup(items)            # يُبنى مرة واحدة لكل الإذاعة
    await state.clear()                          # يمنع ضغط «إرسال» مرتين
    await call.answer("جاري الإرسال...")
    conn = await db()
    try:
        if kind == "customers":
            owner = bc.get("owner") or await settings_owner(call.from_user.id)
            rows = await conn.execute_fetchall(
                "SELECT connection_id, chat_id FROM customers WHERE connection_id IN "
                "(SELECT connection_id FROM business WHERE user_id=?)", (owner,))
            targets = [(r["chat_id"], r["connection_id"]) for r in rows]
        elif kind == "bot":
            rows = await conn.execute_fetchall("SELECT user_id FROM bot_users WHERE user_id!=? ORDER BY user_number", (OWNER_ID,))
            targets = [(r["user_id"], None) for r in rows]
        else:
            rows = await conn.execute_fetchall("SELECT chat_id FROM bot_channels ORDER BY added_at")
            targets = [(r["chat_id"], None) for r in rows if r["chat_id"] in selected]   # المحددة فقط
    finally:
        await conn.close()
    sent = failed = 0
    for chat_id, connection_id in targets:
        ok = False
        for attempt in (1, 2):
            try:
                await _bc_send_one(call.bot, chat_id, bc, markup, connection_id)
                ok = True
                break
            except _RRetryAfter as exc:         # FloodWait: لم تُرسل بعد، ننتظر ونعيد مرة واحدة فقط
                if attempt == 1:
                    await asyncio.sleep(float(getattr(exc, "retry_after", 1)) + 0.5)
                    continue
                logger.warning("إذاعة: FloodWait متكرر للمحادثة %s", chat_id)
            except Exception as exc:            # أي فشل لمستلم واحد لا يوقف الإذاعة
                logger.warning("إذاعة: فشل الإرسال إلى %s (%s): %s", chat_id, type(exc).__name__, exc)
            break
        sent += 1 if ok else 0
        failed += 0 if ok else 1
    fail_txt = f"\nفشل: <b>{failed}</b>" if failed else ""
    if kind == "customers":
        msg = f"تم الإرسال إلى {sent} عميل.{fail_txt}"
    elif kind == "bot":
        msg = f"تم إرسال إذاعة البوت إلى <b>{sent}</b> مستخدم.{fail_txt}"
    else:
        msg = f"تم إرسال الإذاعة إلى <b>{sent}</b> قناة.{fail_txt}"
    await call.message.answer(msg, reply_markup=back_kb("admin_broadcast_section"), parse_mode="HTML")


@router.callback_query(F.data.startswith("bcb_"))
async def bc_text_button(call: CallbackQuery):
    text = await get_bot_message("__bcb_" + call.data[len("bcb_"):])
    if not text:
        await call.answer("النص غير متاح.", show_alert=True)
        return
    try:
        await call.message.answer(text, business_connection_id=getattr(call.message, "business_connection_id", None), parse_mode="HTML")
    except Exception:
        logger.warning("تعذر إرسال نص زر الإذاعة", exc_info=True)
        await call.answer("تعذر إرسال النص.", show_alert=True)
        return
    await call.answer()


@router.callback_query(F.data == "rich_probe_ok")
async def rich_probe_ok(call: CallbackQuery):
    await call.answer("Rich Message يعمل ✔", show_alert=True)



# ═══════════════════════════════════════════════════════════════════════════
# 1) الإحصائيات: قائمة + إحصائيات العملاء (الحالية) + إحصائيات Rich (مع تشغيل/إيقاف)
# ═══════════════════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin_stats")
async def admin_stats_menu(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إحصائيات العملاء", callback_data="admin_stats_clients", style="primary", icon_custom_emoji_id="5778145208411624388")],
        [InlineKeyboardButton(text="إحصائيات Rich", callback_data="admin_stats_rich", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text="رجوع", callback_data="admin_panel", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])
    await edit_or_replace(call, "<b>الإحصائيات</b>\n\nاختر نوع الإحصائيات.", kb)
    await call.answer()


def _rich_stats_text():
    s = lambda k: _RICH_STATS.get(k, 0)
    on = "مفعّل" if _RICH_RT["enabled"] else "متوقف"
    nt = "مفعّلة" if _RICH_RT["notify"] else "متوقفة"
    return ("<b>إحصائيات Rich</b>\n\n"
            f"رسائل Rich ناجحة: <b>{s('ok')}</b>\n"
            f"مرفوضة ورجعت للأزرار العادية: <b>{s('fallback')}</b>\n"
            f"حسابات/محادثات لا تدعم Rich (أزرار عادية): <b>{s('account_unsupported')}</b>\n"
            f"تم تخطيها (حساب غير مدعوم أو إيقاف مؤقت): <b>{s('skipped')}</b>\n"
            f"بنية أزرار غير مدعومة: <b>{s('unsupported')}</b>\n"
            f"أخطاء محادثة (حظر/غير موجودة): <b>{s('chat_errors')}</b>\n\n"
            f"حالة Rich: <b>{on}</b>\nالإخطارات: <b>{nt}</b>")


def _rich_stats_kb():
    en, nt = _RICH_RT["enabled"], _RICH_RT["notify"]
    ok, off = "6206479140040743133", "6206110936789423908"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="إيقاف Rich" if en else "تشغيل Rich", callback_data="rich_tg_enabled",
                              style="danger" if en else "success", icon_custom_emoji_id=off if en else ok)],
        [InlineKeyboardButton(text="إيقاف الإخطارات" if nt else "تشغيل الإخطارات", callback_data="rich_tg_notify",
                              style="danger" if nt else "success", icon_custom_emoji_id=off if nt else ok)],
        [InlineKeyboardButton(text="رجوع", callback_data="admin_stats", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])


@router.callback_query(F.data == "admin_stats_rich")
async def admin_stats_rich(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    await edit_or_replace(call, _rich_stats_text(), _rich_stats_kb())
    await call.answer()


@router.callback_query(F.data.in_({"rich_tg_enabled", "rich_tg_notify"}))
async def rich_toggle(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    key = "enabled" if call.data == "rich_tg_enabled" else "notify"
    _RICH_RT[key] = not _RICH_RT[key]
    await rich_state_save_now()
    await edit_or_replace(call, _rich_stats_text(), _rich_stats_kb())
    await call.answer("تم التغيير.")


# ═══════════════════════════════════════════════════════════════════════════
# 2) إذاعة القنوات: اختيار القنوات المطلوبة (أخضر = محددة، أحمر = غير محددة)
# ═══════════════════════════════════════════════════════════════════════════
CHB_PER_PAGE = 8


async def _chb_render(call, state, page=0):
    data = await state.get_data()
    chans, sel = data.get("chb_list") or [], set(data.get("chb_sel") or [])
    pages = max(1, (len(chans) + CHB_PER_PAGE - 1) // CHB_PER_PAGE)
    page = max(0, min(page, pages - 1))
    rows = []
    for idx in range(page * CHB_PER_PAGE, min(len(chans), (page + 1) * CHB_PER_PAGE)):
        ch = chans[idx]
        rows.append([InlineKeyboardButton(text=ch["title"][:60], callback_data=f"chb_t_{idx}_{page}",
                                          style="success" if ch["id"] in sel else "danger")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀ السابق", callback_data=f"chb_p_{page - 1}", style="primary"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="التالي ▶", callback_data=f"chb_p_{page + 1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="تحديد الكل", callback_data=f"chb_all_{page}", style="success"),
                 InlineKeyboardButton(text="إلغاء الكل", callback_data=f"chb_none_{page}", style="danger")])
    rows.append([InlineKeyboardButton(text=f"متابعة ({len(sel)})", callback_data="chb_go", style="primary")])
    rows.append([InlineKeyboardButton(text="إلغاء", callback_data="home", style="danger", icon_custom_emoji_id="5447647474984449520")])
    text = (f"<b>اختيار قنوات الإذاعة</b>\n\nعدد القنوات: <b>{len(chans)}</b> — المحددة: <b>{len(sel)}</b>\n"
            "اضغط على القناة لتحديدها (أخضر) أو لإلغاء تحديدها (أحمر).")
    await edit_or_replace(call, text, InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "admin_channel_broadcast")
async def admin_channel_broadcast(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("هذه الخاصية للمالك فقط.", show_alert=True)
        return
    conn = await db()
    try:
        rows = await conn.execute_fetchall("SELECT chat_id, title, username FROM bot_channels ORDER BY added_at")
    finally:
        await conn.close()
    if not rows:
        await call.answer("البوت غير مرفوع كأدمن في أي قناة.", show_alert=True)
        return
    chans = [{"id": r["chat_id"], "title": (r["title"] or r["username"] or str(r["chat_id"]))} for r in rows]
    await state.set_state(None)
    await state.update_data(chb_list=chans, chb_sel=[], chb_names=[], bc=None, bc_buttons=[], bted=None)
    await _chb_render(call, state, 0)
    await call.answer()


@router.callback_query(F.data.startswith("chb_t_"))
async def chb_toggle(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    try:
        _, _, idx, page = call.data.split("_")
        idx, page = int(idx), int(page)
    except ValueError:
        await call.answer()
        return
    data = await state.get_data()
    chans, sel = data.get("chb_list") or [], list(data.get("chb_sel") or [])
    if idx < 0 or idx >= len(chans):
        await call.answer("انتهت الجلسة، افتح الإذاعة من جديد.", show_alert=True)
        return
    cid = chans[idx]["id"]
    sel.remove(cid) if cid in sel else sel.append(cid)
    await state.update_data(chb_sel=sel)
    await _chb_render(call, state, page)
    await call.answer()


@router.callback_query(F.data.startswith("chb_p_"))
async def chb_page(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await _chb_render(call, state, int(call.data.rsplit("_", 1)[-1]))
    await call.answer()


@router.callback_query(F.data.startswith("chb_all_") | F.data.startswith("chb_none_"))
async def chb_all_none(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    data = await state.get_data()
    chans = data.get("chb_list") or []
    await state.update_data(chb_sel=[c["id"] for c in chans] if call.data.startswith("chb_all_") else [])
    await _chb_render(call, state, int(call.data.rsplit("_", 1)[-1]))
    await call.answer()


@router.callback_query(F.data == "chb_go")
async def chb_go(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    data = await state.get_data()
    chans, sel = data.get("chb_list") or [], set(data.get("chb_sel") or [])
    if not sel:
        await call.answer("حدّد قناة واحدة على الأقل.", show_alert=True)
        return
    names = [c["title"] for c in chans if c["id"] in sel]
    await state.update_data(chb_names=names)
    await state.set_state(ChannelBroadcastSG.add_text)
    await edit_or_replace(call, f"<b>تم اختيار {len(sel)} قناة.</b>\n\nأرسل النص أو الصورة أو الفيديو أو الصوت أو الملف.", cancel_kb())
    await call.answer()


# ═══════════════════════════════════════════════════════════════════════════
# 3) رسالة غير المشتركين (الاشتراك المدفوع) — قابلة للتعديل من قسم الاشتراكات
# ═══════════════════════════════════════════════════════════════════════════
PAID_GATE_KEY = "__paidgate__"


def _paid_gate_default():
    return {
        "text": ("⛔️ عذراً، لقد انتهى اشتراكك\n\n"
                 "يمكنك الاشتراك مجدداً عبر محفظة Gram (TON) وسيتم تجديد الاشتراك بمجرد التأكيد معي ، أو التواصل معي\n\n"
                 "↖️اضغط على الأزرار بالأسفل :"),
        "buttons": [
            {"label": "Ton-Gram", "type": "text", "color": "primary", "icon_custom_emoji_id": "", "row": 0,
             "value": "قم بتحويل 1 TON إلى المحفظة:\n<code>UQDfrY4EpVHzTGUpUVWSswIu1z5RgOlpOko1dukQMfkLrKbc</code>\n\nوأرسل سكرين التحويل."},
            {"label": "VF", "type": "text", "color": "primary", "icon_custom_emoji_id": "", "row": 1,
             "value": "قم بتحويل 50 EGP إلى الرقم التالي:\n<code>01040851504</code>\n\nوأرسل سكرين التحويل."},
            {"label": "دعوة اشخاص", "type": "text", "color": "success", "icon_custom_emoji_id": "", "row": 2,
             "value": ("يمكنك دعوه اشخاص لتمديد اشتراك البوت لايام اكثر\n\n"
                       "كل شخص تدعيه للبوت يتم تمديد اشتراك البوت لـ 1 يوم\n\n"
                       "لاحتساب الاحاله يجب من الشخص الذي دعوته ان يربط البوت في حسابه\n\n"
                       "رابط الإحالة الخاص بك:\n<code>{ref_link}</code>")},
            {"label": "دفع طريقة اخرى", "type": "url", "color": "primary", "icon_custom_emoji_id": "", "row": 3,
             "value": DEVELOPER_URL},
        ],
    }


async def _paid_gate_load():
    default = _paid_gate_default()
    try:
        raw = await get_bot_message(PAID_GATE_KEY)
        cfg = json.loads(raw) if raw else None
    except Exception:
        cfg = None
    if not isinstance(cfg, dict):
        return default
    buttons = cfg["buttons"] if isinstance(cfg.get("buttons"), list) else default["buttons"]
    # تنظيف رسالة دعوة الأشخاص من الإيموجيز في النص المحفوظ والافتراضي؛
    # يُستخدم النص نفسه في المعاينة وعند عرضه للمستخدم.
    for button in buttons:
        if not isinstance(button, dict):
            continue
        if (button.get("label") or "").strip() == "دعوة اشخاص":
            value = str(button.get("value") or "")
            value = re.sub(r"<tg-emoji\b[^>]*>.*?</tg-emoji>", "", value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\uFE0F\u200D]", "", value)
            button["value"] = value
    # ترحيل نصوص الدفع القديمة فقط (إن كانت القيمة المحفوظة تساوي الافتراضي القديم حرفيًا)،
    # أما أي تعديل تجريه من «إدارة الأزرار» فيبقى كما هو ولا يُستبدل.
    _old_values = {
        "قم بتحويل 1 TON إلى المحفظة:\n<code>UQDfrY4EpVHzTGUpUVWSswIu1z5RgOlpOko1dukQMfkLrKbc</code>": 0,
        "قم بتحويل 50 EGP إلى الرقم التالي:\n<code>01040851504</code>": 1,
    }
    for button in buttons:
        if not isinstance(button, dict):
            continue
        idx = _old_values.get(str(button.get("value") or "").strip())
        if idx is not None:
            button["value"] = default["buttons"][idx]["value"]
    return {"text": cfg.get("text") or default["text"], "buttons": buttons}


async def _paid_gate_save(cfg):
    await set_bot_message(PAID_GATE_KEY, json.dumps(cfg, ensure_ascii=False))


def _paid_gate_markup(cfg):
    rows, last = [], None
    for i, b in enumerate(cfg["buttons"]):
        it = _bted_norm(b)
        row = b.get("row") if isinstance(b.get("row"), int) else i
        base = {"text": it["label"], "style": BTN_STYLE_MAP.get(it["color"], "primary")}
        if it["icon_custom_emoji_id"]:
            base["icon_custom_emoji_id"] = it["icon_custom_emoji_id"]
        if it["type"] == "url":
            base["url"] = it["value"]
        elif it["type"] == "copy":
            base["copy_text"] = CopyTextButton(text=it["value"])
        else:
            base["callback_data"] = f"pgb_{i}"
        btn = InlineKeyboardButton(**base)
        if rows and row == last:
            rows[-1].append(btn)
        else:
            rows.append([btn])
            last = row
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


async def _paid_gate_send(target):
    cfg = await _paid_gate_load()
    await target.answer(cfg["text"], reply_markup=_paid_gate_markup(cfg), parse_mode="HTML")


@router.callback_query(F.data.startswith("pgb_"))
async def paid_gate_button(call: CallbackQuery):
    arg = call.data[len("pgb_"):]
    cfg = await _paid_gate_load()
    if arg == "back":
        await edit_or_replace(call, cfg["text"], _paid_gate_markup(cfg))
        await call.answer()
        return
    try:
        b = cfg["buttons"][int(arg)]
    except (ValueError, IndexError):
        await call.answer("غير متاح.", show_alert=True)
        return
    me = await call.bot.me()
    text = ((b.get("value") or "")
            .replace("{ref_link}", f"https://t.me/{me.username}?start=ref_{call.from_user.id}")
            .replace("{user_id}", str(call.from_user.id))
            .replace("{bot_username}", me.username or ""))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="𓏺 𝖤𝖫 𝖹𝖮𝖹 .", url=DEVELOPER_URL,
            style="success", icon_custom_emoji_id="6206155797722830770")],
        [InlineKeyboardButton(
            text="رجوع", callback_data="pgb_back", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])
    await edit_or_replace(call, text, kb)
    await call.answer()


class PaidGateSG(StatesGroup):
    text = State()


def _paidgate_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تعديل النص", callback_data="paidgate_text", style="primary")],
        [InlineKeyboardButton(text="إدارة الأزرار", callback_data="bted_open_paidgate_0", style="primary", icon_custom_emoji_id="6039450962865688331")],
        [InlineKeyboardButton(text="معاينة", callback_data="paidgate_prev", style="primary", icon_custom_emoji_id="6037397706505195857")],
        [InlineKeyboardButton(text="استعادة الافتراضي", callback_data="paidgate_reset", style="danger", icon_custom_emoji_id="6039522349517115015")],
        [InlineKeyboardButton(text="رجوع", callback_data="admin_subscription_section", style="danger", icon_custom_emoji_id="5445365692004071819")],
    ])


@router.callback_query(F.data == "paidgate_menu")
async def paidgate_menu(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.set_state(None)
    await edit_or_replace(call, "<b>رسالة غير المشتركين</b>\n\nتظهر للمستخدم أول ما يضغط /start وهو غير مشترك (في الوضع المدفوع).\nيمكنك استخدام {ref_link} و{user_id} و{bot_username} داخل نص أي زر.", _paidgate_menu_kb())
    await call.answer()


@router.callback_query(F.data == "paidgate_text")
async def paidgate_text(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        return
    await state.set_state(PaidGateSG.text)
    await edit_or_replace(call, "أرسل نص الرسالة الجديد (يدعم التنسيق والإيموجي المميز).", cancel_kb("paidgate_menu"))
    await call.answer()


@router.message(PaidGateSG.text)
async def paidgate_text_msg(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    text = (message.html_text or "").strip()
    if not text:
        await message.answer("أرسل نصًا صحيحًا.")
        return
    cfg = await _paid_gate_load()
    cfg["text"] = text
    await _paid_gate_save(cfg)
    await state.set_state(None)
    await message.answer("<b>تم حفظ نص الرسالة.</b>", reply_markup=back_kb("paidgate_menu"), parse_mode="HTML")


@router.callback_query(F.data == "paidgate_prev")
async def paidgate_prev(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    await _paid_gate_send(call.message)
    await call.answer("هذه الرسالة كما ستظهر للمستخدم.")


@router.callback_query(F.data == "paidgate_reset")
async def paidgate_reset(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    await set_bot_message(PAID_GATE_KEY, "")
    await call.answer("تمت استعادة الرسالة الافتراضية.", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════
# 4) نظام الدعوات: start=ref_<id> → عند ربط المدعو حسابه يُمدَّد اشتراك الداعي يومًا (مرة واحدة لكل مدعو)
#    التخزين في bot_messages بمفاتيح __refby_<invited> و__refdone_<invited> (دون تغيير بنية الجداول).
# ═══════════════════════════════════════════════════════════════════════════
_REF_RE = re.compile(r"^ref_(\d{3,15})$")


async def _referral_register(message):
    try:
        parts = (message.text or "").split(maxsplit=1)
        m = _REF_RE.match(parts[1].strip()) if len(parts) > 1 else None
        if not m:
            return
        referrer, uid = int(m.group(1)), message.from_user.id
        if referrer == uid:
            return
        conn = await db()
        try:
            row = await fetchone(conn, "SELECT 1 FROM bot_users WHERE user_id=?", (referrer,))
        finally:
            await conn.close()
        if row:
            await set_bot_message(f"__refby_{uid}", str(referrer))
    except Exception:
        logger.warning("تعذر تسجيل الإحالة", exc_info=True)


async def _referral_reward(bot, invited):
    try:
        referrer = (await get_bot_message(f"__refby_{invited}") or "").strip()
        if not referrer.isdigit() or await get_bot_message(f"__refdone_{invited}"):
            return
        await set_bot_message(f"__refdone_{invited}", "1")          # مرة واحدة فقط لكل مدعو
        referrer, now = int(referrer), datetime.now(timezone.utc)
        conn = await db()
        try:
            row = await fetchone(conn, "SELECT expires_at FROM bot_subscriptions WHERE user_id=?", (referrer,))
            base = now
            if row:
                try:
                    base = max(now, datetime.fromisoformat(row["expires_at"]))
                except Exception:
                    base = now
            new_exp = base + timedelta(days=1)
            await conn.execute(
                "INSERT INTO bot_subscriptions(user_id,expires_at,trial,created_at) VALUES(?,?,1,?) "
                "ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at",
                (referrer, new_exp.isoformat(), now.isoformat()))
            await conn.commit()
        finally:
            await conn.close()
        try:
            await bot.send_message(referrer, "<tg-emoji emoji-id='6206378324273403309'>🎉</tg-emoji> ربط أحد الأشخاص الذين دعوتهم حسابه بالبوت، وتم تمديد اشتراكك يومًا.")
        except Exception:
            pass
    except Exception:
        logger.warning("تعذر تنفيذ مكافأة الإحالة", exc_info=True)


@router.message(F.text)
async def transfer_codes_message(message: Message, state: FSMContext):
    if await state.get_state():
        return
    text = (message.text or "").strip()
    normalized = text.lower()
    conn = await db()
    rows = await conn.execute_fetchall(
        "SELECT id, trigger, response FROM replies WHERE owner_id=? ORDER BY id ASC",
        (OWNER_ID,),
    )
    for row in rows:
        if normalized == (row["trigger"] or "").lower().strip():
            btns = await conn.execute_fetchall(
                "SELECT id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value "
                "FROM reply_buttons WHERE reply_id=? ORDER BY position", (row["id"],)
            )
            await conn.close()
            try:
                await message.delete()
            except Exception:
                logger.debug("Could not delete trigger message in regular chat", exc_info=True)
            await message.answer(
                row["response"], reply_markup=build_reply_kb(btns) or None, parse_mode="HTML"
            )
            return
    await conn.close()
    parsed = parse_transfer_request(message.text)
    if not parsed:
        return
    phone, amount = parsed
    codes = transfer_codes(phone, amount)
    await message.answer(
        transfer_codes_text(phone, amount, codes),
        reply_markup=transfer_codes_kb(codes),
        parse_mode="HTML",
    )
# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ

@router.callback_query(F.data.startswith("rtext_"))
async def reply_text_button(call: CallbackQuery):
    try: bid=int(call.data[len("rtext_"):])
    except Exception: await call.answer(); return
    conn=await db(); row=await fetchone(conn, "SELECT btn_value FROM reply_buttons WHERE id=? AND btn_type='text'", (bid,)); await conn.close()
    if not row: await call.answer("النص غير موجود", show_alert=True); return
    await call.message.edit_text(row["btn_value"], reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="رجوع", callback_data=f"reply_back_{bid}", style="danger", icon_custom_emoji_id="5445365692004071819")]]), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("calc_copy_"))
async def calc_copy(call: CallbackQuery):
    result = call.data[len("calc_copy_"):]
    try:
        await call.answer(f"انسخ الإجابة:\n{result}", show_alert=True)
    except Exception:
        await call.answer()

@router.callback_query(F.data.startswith("reply_back_"))
async def reply_back(call: CallbackQuery):
    try:
        button_id = int(call.data[len("reply_back_"):])
    except ValueError:
        await call.answer()
        return
    conn = await db()
    row = await fetchone(
        conn,
        "SELECT rb.reply_id, r.response FROM reply_buttons rb "
        "JOIN replies r ON r.id=rb.reply_id WHERE rb.id=?",
        (button_id,)
    )
    buttons = await conn.execute_fetchall(
        "SELECT id, label, btn_type, btn_color, icon_custom_emoji_id, btn_value "
        "FROM reply_buttons WHERE reply_id=? ORDER BY position",
        (row["reply_id"],)
    ) if row else []
    await conn.close()
    if row:
        await call.message.edit_text(row["response"], reply_markup=build_reply_kb(buttons), parse_mode="HTML")
    else:
        await call.message.delete()
    await call.answer()

@router.callback_query(F.data.startswith("rcopy_"))
async def reply_copy_button(call: CallbackQuery):
    parts = call.data.split("_", 1)
    if len(parts) < 2:
        await call.answer()
        return
    try:
        button_id = int(parts[1])
    except ValueError:
        await call.answer()
        return
    conn = await db()
    row = await fetchone(conn,
        "SELECT btn_value FROM reply_buttons WHERE id=? AND btn_type='copy' LIMIT 1",
        (button_id,))
    await conn.close()
    if row:
        await call.answer(f"انسخ هذا النص:\n{row['btn_value']}", show_alert=True)
    else:
        await call.answer()

# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
async def bold_outgoing_text_middleware(make_request, bot, method):
    fields = getattr(type(method), "model_fields", {})
    changes = {}
    text_fields = (
        ("text", "parse_mode", "entities"),
        ("caption", "parse_mode", "caption_entities"),
        ("question", "question_parse_mode", "question_entities"),
        ("explanation", "explanation_parse_mode", "explanation_entities"),
        ("description", "description_parse_mode", "description_entities"),
    )
    for text_field, mode_field, entities_field in text_fields:
        if text_field not in fields or mode_field not in fields:
            continue
        value = getattr(method, text_field, None)
        if not isinstance(value, str) or not value.strip():
            continue
        if entities_field in fields and getattr(method, entities_field, None):
            continue
        changes[text_field] = value if "<blockquote>" in value else f"<blockquote><b>{value}</b></blockquote>"
        changes[mode_field] = ParseMode.HTML
    if changes:
        method = method.model_copy(update=changes)
    return await make_request(bot, method)


# الترخيص بواسطه: @Z0_E0
# العلامة التجارية: EL ZOZ 
# حقوق الطبع والنشر: © 2026 EL ZOZ
async def main():
    await init_db()
    await init_extra_features()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.session.middleware.register(bold_outgoing_text_middleware)
    bot.session.middleware.register(rich_buttons_middleware)
    await load_row_map()
    await rich_state_load()
    await rich_startup_probe(bot)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    background_tasks = [
        asyncio.create_task(live_clock_worker(bot)),
        asyncio.create_task(live_bio_worker(bot)),
        asyncio.create_task(scheduled_worker(bot)),
    ]
    print(f"{BOT_NAME} is running...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message", "callback_query",
                "business_connection", "business_message",
                "edited_business_message", "deleted_business_messages", "my_chat_member"
            ]
        )
    finally:
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        await bot.session.close()

if __name__ == "__main__":
    if not TC_SESSION:
        print("تنبيه: TC_SESSION غير مضبوط؛ ميزة Truecaller ستكون معطلة.")
    asyncio.run(main())
print("""

╔══════════════════════════════════════════════════════════╗
║                        E L   Z O Z                       ║
║                   TELEGRAM BUSINESS BOT                  ║
║                     DEV BY : @Z0_E0                      ║
╚══════════════════════════════════════════════════════════╝
""")
