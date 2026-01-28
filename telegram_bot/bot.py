import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    filters,
)

from config import BOT_TOKEN

# ================= CONFIG =================
DATA_FILE = "users.json"
AFFILIATE_ID = "bh7162"

# ================= STORAGE =================
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ================= HELPERS =================
URL_RE = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>\"']+)")

def extract_links(text: str):
    if not text:
        return []

    links = []
    for m in URL_RE.findall(text):
        url = m.strip()
        url = url.rstrip(").,!?;:\"'”’]}>")  # strip trailing punctuation

        if url.lower().startswith("www."):
            url = "https://" + url

        links.append(url)

    # de-duplicate preserving order
    seen = set()
    out = []
    for u in links:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

def convert_to_dl_link_param1(original_url: str, affiliate_id: str, token: str) -> str:
    """Return ONLY the dl.flipkart.com link with affExtParam1."""
    parsed = urlparse(original_url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL")

    qs = parse_qs(parsed.query)
    base = {k: v[0] for k, v in qs.items()}

    base["affid"] = affiliate_id
    base["affExtParam1"] = token

    path = parsed.path or "/"
    if not path.startswith("/dl"):
        path = "/dl" + path

    return urlunparse((
        "https",
        "dl.flipkart.com",
        path,
        "",
        urlencode(base),
        ""
    ))

def normalize_channel_input(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    if not s:
        return s
    if s.startswith("@"):
        return s
    if s.lstrip("-").isdigit():
        return s
    return "@" + s

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome!\n\n"
        "STEP 1: Set token\n"
        "  /settoken YOUR_TOKEN\n\n"
        "STEP 2: Set channel\n"
        "  /setchannel @channelusername  OR  /setchannel -100xxxxxxxxxx\n\n"
        "STEP 3: Send Flipkart links\n\n"
        "Note: Add the bot to the CHANNEL as ADMIN and enable 'Post messages'."
    )

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage:\n/settoken YOUR_TOKEN")
        return

    token = context.args[0].strip()
    user = update.effective_user
    user_id = str(user.id)

    users = load_users()
    if user_id not in users:
        users[user_id] = {"username": user.username or f"user_{user.id}"}

    users[user_id]["token"] = token
    save_users(users)

    await update.message.reply_text("✅ Token saved successfully.")

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/setchannel @yourchannelusername\n"
            "or\n"
            "/setchannel -1001234567890"
        )
        return

    users = load_users()
    user_id = str(update.effective_user.id)

    if user_id not in users or not users[user_id].get("token"):
        await update.message.reply_text("❌ First set your token using /settoken YOUR_TOKEN")
        return

    channel_input = normalize_channel_input(context.args[0])

    try:
        chat = await context.bot.get_chat(channel_input)
        channel_id = str(chat.id)
    except Forbidden:
        await update.message.reply_text(
            "❌ Forbidden: Bot cannot access this channel.\n"
            "Fix: Add bot to the CHANNEL as ADMIN and allow 'Post messages'."
        )
        return
    except BadRequest as e:
        await update.message.reply_text(
            f"❌ BadRequest: {e}\n"
            "Fix: check channel username/id and ensure bot is added to that channel."
        )
        return

    users[user_id]["channel_id"] = channel_id
    save_users(users)

    await update.message.reply_text(
        f"✅ Channel linked:\nTitle: {chat.title}\nID: {channel_id}"
    )

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)

    if user_id in users and "channel_id" in users[user_id]:
        users[user_id].pop("channel_id", None)
        save_users(users)
        await update.message.reply_text("🗑 Channel removed.")
    else:
        await update.message.reply_text("❌ No channel linked.")

async def test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)

    if user_id not in users or "channel_id" not in users[user_id]:
        await update.message.reply_text("❌ No channel linked.")
        return

    channel_id = users[user_id]["channel_id"]

    try:
        chat = await context.bot.get_chat(channel_id)
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)

        await update.message.reply_text(
            "✅ Channel reachable.\n"
            f"Title: {chat.title}\n"
            f"ID: {chat.id}\n"
            f"Bot status: {bot_member.status}"
        )

        await context.bot.send_message(chat_id=chat.id, text="✅ Test post from bot.")
        await update.message.reply_text("✅ Test message sent to channel.")
    except Forbidden as e:
        await update.message.reply_text(
            f"❌ Forbidden: {e}\n"
            "Fix: Add bot to the CHANNEL as ADMIN + allow 'Post messages'."
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ BadRequest: {e}")

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    user_id = str(update.effective_user.id)

    users = load_users()
    token = users.get(user_id, {}).get("token")
    if not token:
        await update.message.reply_text("❌ Token not set. Use /settoken YOUR_TOKEN")
        return

    links = extract_links(text)
    if not links:
        await update.message.reply_text(
            "❌ No links found.\nSend a message containing a link like:\nhttps://www.flipkart.com/..."
        )
        return

    channel_id = users.get(user_id, {}).get("channel_id")

    outputs = []
    for link in links:
        try:
            converted = convert_to_dl_link_param1(link, AFFILIATE_ID, token)
        except Exception:
            continue

        message = f"{converted}"
        outputs.append(message)

        # AUTO POST (if channel linked)
        if channel_id:
            try:
                await context.bot.send_message(chat_id=int(channel_id), text=message)
            except Exception as e:
                await update.message.reply_text(
                    f"⚠️ Failed to post in channel.\nError: {e}\nUse /testchannel to diagnose."
                )

    if not outputs:
        await update.message.reply_text("❌ No valid URLs could be processed from your message.")
        return

    await update.message.reply_text("\n\n━━━━━━━━━━━━━━\n\n".join(outputs))

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settoken", set_token))
    app.add_handler(CommandHandler("setchannel", set_channel))
    app.add_handler(CommandHandler("removechannel", remove_channel))
    app.add_handler(CommandHandler("testchannel", test_channel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()