import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters,
)

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

TUR, SONI, ISM, TEL, MANZIL = range(5)

TURLAR = [["Erkaklar naskisi", "Ayollar naskisi"], ["Bolalar naskisi", "Aralash"]]
MENU = ReplyKeyboardMarkup([["🛒 Buyurtma berish"]], resize_keyboard=True)


class Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *a):
        pass


def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Ping).serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! 🧦 Optom naskilar do'konimizga xush kelibsiz.\n"
        "Buyurtma berish uchun tugmani bosing.",
        reply_markup=MENU,
    )


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Qaysi turdagi naski kerak?",
        reply_markup=ReplyKeyboardMarkup(TURLAR, resize_keyboard=True, one_time_keyboard=True),
    )
    return TUR


async def get_tur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tur"] = update.message.text
    await update.message.reply_text(
        "Necha dona (juft) kerak? Raqam yozing. Masalan: 100",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SONI


async def get_soni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["soni"] = update.message.text
    await update.message.reply_text("Ismingizni yozing:")
    return ISM


async def get_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ism"] = update.message.text
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Telefon raqamingizni yuboring (tugma yoki qo'lda yozing):", reply_markup=kb
    )
    return TEL


async def get_tel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["tel"] = update.message.contact.phone_number
    else:
        context.user_data["tel"] = update.message.text
    await update.message.reply_text(
        "Manzilingizni yozing (viloyat, tuman):", reply_markup=ReplyKeyboardRemove()
    )
    return MANZIL


async def get_manzil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    d["manzil"] = update.message.text
    user = update.effective_user
    text = (
        "🆕 YANGI BUYURTMA\n\n"
        f"🧦 Tur: {d['tur']}\n"
        f"🔢 Soni: {d['soni']}\n"
        f"👤 Ism: {d['ism']}\n"
        f"📞 Tel: {d['tel']}\n"
        f"📍 Manzil: {d['manzil']}\n"
        f"💬 Telegram: @{user.username or 'yoq'} (ID: {user.id})"
    )
    await context.bot.send_message(ADMIN_ID, text)
    await update.message.reply_text(
        "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=MENU,
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.", reply_markup=MENU)
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Buyurtma berish$"), order_start)],
        states={
            TUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tur)],
            SONI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_soni)],
            ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ism)],
            TEL: [MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.CONTACT, get_tel)],
            MANZIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_manzil)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    threading.Thread(target=run_web, daemon=True).start()
    app.run_polling()


if __name__ == "__main__":
    main()
