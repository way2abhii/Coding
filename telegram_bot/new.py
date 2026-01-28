import json
import os
import re
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

def convert_to_dl_links(url: str, affiliate_id: str, token: str):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    base = {k: v[0] for k, v in qs.items()}
    base["affid"] = affiliate_id

    path = parsed.path
    if not path.startswith("/dl"):
        path = "/dl" + path

    def build(extra=None):
        params = base.copy()
        if extra:
            params.update(extra)
        return urlunparse((
            "https",
            "dl.flipkart.com",
            path,
            "",
            urlencode(params),
            ""
        ))

    return (
        build(),
        build({"affExtParam1": token}),
        build({"affExtParam1": token, "affExtParam2": "102"})
    )

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    await update.message.reply_text(
        "👋 Welcome (CHANNEL MODE)\n\n"
        "STEP 1️⃣ Send your token (affExtParam1)\n"
        "STEP 2️⃣ Use /setchannel <channel_id>\n"
        "STEP 3️⃣ Send Flipkart links\n\n"
        "ℹ️ Channel ID looks like: -1001234567890"
    )

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "❌ Use this command in BOT DM only."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n/setchannel -1001234567890"
        )
        return

    channel_id = context.args[0]

    if not channel_id.startswith("-100"):
        await update.message.reply_text(
            "❌ Invalid channel ID.\n"
            "It must start with -100"
        )
        return

    users = load_users()
    user_id = str(update.message.from_user.id)

    if user_id not in users:
        await update.message.reply_text(
            "❌ First send your token."
        )
        return

    users[user_id]["channel_id"] = channel_id
    save_users(users)

    await update.message.reply_text(
        f"✅ Channel linked successfully:\n{channel_id}\n\n"
        "Now send Flipkart links in DM."
    )

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()
    user_id = str(update.message.from_user.id)

    users = load_users()

    # Save token first time
    if user_id not in users:
        users[user_id] = {
            "token": text
        }
        save_users(users)
        await update.message.reply_text(
            "✅ Token saved.\nNow set channel using /setchannel"
        )
        return

    token = users[user_id]["token"]
    channel_id = users[user_id].get("channel_id")

    links = extract_links(text)
    if not links:
        await update.message.reply_text("❌ No links found.")
        return

    for link in links:
        normal, sub1, sub2 = convert_to_dl_links(
            link, AFFILIATE_ID, token
        )

        message = (
            # "🔹 Normally converted:\n"
            # f"{normal}\n\n"
            "🔹 Added sub id with affExtParam1:\n"
            f"{sub1}\n\n"
            # "🔹 Added sub id with affExtParam1 & affExtParam2:\n"
            # f"{sub2}"
        )

        # Reply in DM
        await update.message.reply_text(message)

        # Auto-post to CHANNEL
        if channel_id:
            try:
                await context.bot.send_message(
                    chat_id=channel_id,
                    text=message
                )
            except Exception:
                await update.message.reply_text(
                    "❌ Bot cannot post to channel.\n"
                    "Make sure:\n"
                    "• Bot is added to CHANNEL (not group)\n"
                    "• Bot is ADMIN with Post Messages permission"
                )

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setchannel", set_channel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot running (CHANNEL MODE ONLY)...")
    app.run_polling()

if __name__ == "__main__":
    main()
