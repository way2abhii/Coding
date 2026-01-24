import json
import os
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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


def expand_url(url: str) -> str:
    """
    Best-effort expansion.
    If expansion fails, returns original URL.
    """
    try:
        r = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code == 200:
            return r.url
        return url
    except Exception:
        return url


def append_affiliate_params(url: str, token: str) -> str:
    """
    Appends affiliate params to ANY URL.
    Removes existing affiliate params to avoid duplicates.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # Remove existing affiliate params
    qs.pop("affid", None)
    qs.pop("affExtParam1", None)
    qs.pop("affExtParam2", None)

    # Add ours
    qs["affid"] = [AFFILIATE_ID]
    qs["affExtParam1"] = [token]
    qs["affExtParam2"] = ["ClickID"]

    final_query = urlencode(qs, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        final_query,
        parsed.fragment
    ))


# ================= is.gd SHORTENER =================
def shorten_url(url: str) -> str:
    try:
        r = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=10
        )
        if r.status_code == 200:
            return r.text.strip()
        return url
    except Exception:
        return url


# ================= COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.message.from_user.id)

    if user_id in users:
        await update.message.reply_text(
            "✅ Token already saved.\nSend any link."
        )
    else:
        await update.message.reply_text(
            "🔑 Send your token (affExtParam1):"
        )


# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    user_id = str(user.id)

    users = load_users()

    # Save token once
    if user_id not in users:
        users[user_id] = {
            "username": user.username or f"user_{user.id}",
            "token": text
        }
        save_users(users)
        await update.message.reply_text(
            "✅ Token saved. Now send any link."
        )
        return

    token = users[user_id]["token"]
    links = extract_links(text)

    if not links:
        await update.message.reply_text("❌ No valid links found.")
        return

    results = []

    for link in links:
        expanded = expand_url(link)
        with_params = append_affiliate_params(expanded, token)
        short = shorten_url(with_params)
        results.append(short)

    await update.message.reply_text("\n\n".join(results))


# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot running (ALL LINKS MODE)...")
    app.run_polling()


if __name__ == "__main__":
    main()
