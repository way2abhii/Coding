import json
import os
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus

from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    filters
)
from telegram import Update
from config import BOT_TOKEN

# ================= CONFIG =================
DATA_FILE = "users.json"
AFFILIATE_ID = "bh7162"

ALLOWED_PARAMS = {
    "pid",
    "lid",
    "marketplace",
    "store",
    "ssid",
    "iid",
    "ppt",
    "ppn",
    "q",
    "srno",
    "qH",
    "cid"
}

# ================= STORAGE =================
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ================= HELPERS =================
def extract_links(text: str):
    return re.findall(r"https?://[^\s]+", text)


def clean_and_parse(url: str):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    clean_qs = {k: v[0] for k, v in qs.items() if k in ALLOWED_PARAMS}
    return parsed, clean_qs


def build_url(parsed, params: dict):
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        urlencode(params),
        ""
    ))


# ================= FKRT SHORTENER (FAST) =================
def shorten_fkrt(url: str) -> str:
    """
    Flipkart shortener ONLY (no fallback).
    Fast timeout.
    """
    try:
        fkrt_try = f"https://fkrt.it/?url={quote_plus(url)}"
        r = requests.get(
            fkrt_try,
            allow_redirects=True,
            timeout=3,  # FAST
            headers={"User-Agent": "Mozilla/5.0"}
        )

        # If real fkrt link generated
        if "fkrt.it/" in r.url and r.url.count("/") <= 3:
            return r.url

        # If Flipkart refuses, return original
        return url

    except Exception:
        return url


# ================= COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.message.from_user.id)

    if user_id in users:
        await update.message.reply_text("✅ Token already saved. Send Flipkart links.")
    else:
        await update.message.reply_text("🔑 Send your token (affExtParam1):")


# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    user_id = str(user.id)

    users = load_users()

    # Save token first
    if user_id not in users:
        users[user_id] = {
            "username": user.username or f"user_{user.id}",
            "token": text
        }
        save_users(users)
        await update.message.reply_text("✅ Token saved. Now send Flipkart links.")
        return

    token = users[user_id]["token"]
    links = extract_links(text)

    if not links:
        await update.message.reply_text("❌ No valid links found.")
        return

    results = []

    for link in links:
        parsed, base_params = clean_and_parse(link)

        # 1️⃣ Normal
        normal_params = base_params.copy()
        normal_params["affid"] = AFFILIATE_ID
        normal_link = shorten_fkrt(build_url(parsed, normal_params))

        # 2️⃣ Sub ID 1
        sub1_params = normal_params.copy()
        sub1_params["affExtParam1"] = token
        sub1_link = shorten_fkrt(build_url(parsed, sub1_params))

        # # 3️⃣ Sub ID 1 + 2
        # sub2_params = sub1_params.copy()
        # sub2_params["affExtParam2"] = "102"
        # sub2_link = shorten_fkrt(build_url(parsed, sub2_params))

        results.append(
            # f"🔹 Normally converted:\n{normal_link}\n\n"
            f"🔹 Added sub id with affExtParam1:\n{sub1_link}\n\n"
            # f"🔹 Added sub id with affExtParam1 & affExtParam2:\n{sub2_link}"
        )

    await update.message.reply_text("\n\n━━━━━━━━━━━━━━\n\n".join(results))


# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("⚡ Fast Flipkart bot running (FKRT ONLY)...")
    app.run_polling()


if __name__ == "__main__":
    main()
