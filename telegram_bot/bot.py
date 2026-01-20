import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from bitlyshortener import Shortener
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

# Bitly Token (replace with your real token)
BITLY_TOKENS = ["ab3200059b349980aeb332261bca1a3a9b01538a"]

# ================= HELPERS =================
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def extract_links(text: str) -> list:
    pattern = r'https?://[^\s]+'
    return re.findall(pattern, text)


# ================= LINK SHORTENER =================
def shorten_url(url: str) -> str:
    try:
        shortener = Shortener(tokens=BITLY_TOKENS, max_cache_size=8192)
        return shortener.shorten_urls([url])[0]
    except Exception:
        # Fail-safe: return original link if Bitly fails
        return url


# ================= AFFILIATE LINK LOGIC =================
def generate_affiliate_link(
    url: str,
    aff_ext_param1: str,
    aff_ext_param2: str = None
) -> str:

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Mandatory affiliate ID
    query_params["affid"] = [AFFILIATE_ID]

    is_product = "/p/" in parsed.path

    keep_keys_product = [
        "pid", "lid", "marketplace", "store", "srno",
        "iid", "ppt", "ppn", "ssid", "otracker1"
    ]

    keep_keys_listing = [
        "sid", "sort", "iid", "ctx", "cid",
        "otracker1", "p[]"
    ]

    if is_product:
        filtered = {k: v for k, v in query_params.items()
                    if k in keep_keys_product or k == "affid"}
        order = [
            "marketplace", "iid", "ppt", "lid",
            "srno", "pid", "affid",
            "store", "ssid", "otracker1", "ppn"
        ]
    else:
        filtered = {k: v for k, v in query_params.items()
                    if k in keep_keys_listing or k == "affid"}
        order = ["affid", "p[]", "sort", "iid", "ctx", "otracker1", "sid", "cid"]

    ordered_params = []
    for k in order:
        if k in filtered:
            for val in filtered[k]:
                ordered_params.append((k, val))

    # Telegram token → affExtParam1
    ordered_params.append(("affExtParam1", aff_ext_param1))

    # Optional sub-id
    if aff_ext_param2:
        ordered_params.append(("affExtParam2", aff_ext_param2))

    final_query = urlencode(ordered_params, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        final_query,
        ""
    ))


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.message.from_user.id)

    if user_id in users:
        await update.message.reply_text(
            "✅ Token already saved.\nSend Flipkart links anytime."
        )
    else:
        await update.message.reply_text(
            "🔑 Please send your unique token (affExtParam1):"
        )


# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or f"user_{user.id}"

    users = load_users()

    # 🔑 Save token
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "token": text
        }
        save_users(users)

        await update.message.reply_text(
            "✅ Token saved successfully!\nNow send Flipkart links."
        )
        return

    token = users[user_id]["token"]

    links = extract_links(text)
    if not links:
        await update.message.reply_text("❌ No valid links found.")
        return

    results = []
    for link in links:
        try:
            affiliate_link = generate_affiliate_link(
                url=link,
                aff_ext_param1=token
            )
            short_link = shorten_url(affiliate_link)
            results.append(short_link)
        except Exception:
            results.append(f"❌ Failed to process:\n{link}")

    await update.message.reply_text("\n\n".join(results))


# ================= RUN BOT =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram Affiliate Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
