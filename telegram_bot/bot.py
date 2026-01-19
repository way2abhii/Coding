from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram import Update
from config import BOT_TOKEN

def is_link(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if not is_link(text):
        await update.message.reply_text("❌ Please send a valid link")
        return

    # username handling
    if user.username:
        username = user.username
    else:
        username = f"user_{user.id}"

    # append username to link
    result = f"{text} {username}"

    await update.message.reply_text(result)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
