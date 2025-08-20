import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")# သင့်ရဲ့ BotFather က token ထည့်ပါ
ADMIN_ID = int(os.getenv("ADMIN_ID"))            # သင့်ရဲ့ Telegram ID ထည့်ပါ

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Conversation States
GAME_ID, PAYMENT_CONFIRMATION = range(2)

# Temporary user data
user_data = {}

# Package List (မင်းပေးထားတဲ့ list အကုန်)
packages = {
    "Weekly Pass": 6100,
    "Twilight Pass": 33000,
    "86 Diamonds": 5100,
    "172 Diamonds": 10000,
    "257 Diamonds": 14400,
    "343 Diamonds": 19300,
    "429 Diamonds": 23900,
    "514 Diamonds": 28600,
    "600 Diamonds": 33500,
    "706 Diamonds": 38400,
    "792 Diamonds": 43300,
    "878 Diamonds": 47900,
    "963 Diamonds": 52800,
    "1049 Diamonds": 57400,
    "1135 Diamonds": 63300,
    "1220 Diamonds": 67300,
    "1412 Diamonds": 77500,
    "2195 Diamonds": 118500,
    "2901 Diamonds": 155500,
    "3688 Diamonds": 195000,
    "5532 Diamonds": 292500,
    "6238 Diamonds": 330000,
    "7366 Diamonds": 386000,
    "9288 Diamonds": 492000,
}

# --- Commands ---

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_text = (
        "👋 မင်္ဂလာပါ Customer ရေ!\n\n"
        "MLBB Diamonds ဝယ်ယူဖို့ ကြိုဆိုပါတယ်ဗျ\n\n"
        "💎 Package ကို အောက်မှာရွေးချယ်နိုင်ပါတယ်။\n"
        "အားပေးမှုအတွက် ကျေးဇူးတင်ပါတယ်ဗျ 🙏\n"
        "ကောင်းသောနေ့လေး ပိုင်ဆိုင်နိုင်ပါစေ 🌸"
    )

    # Inline Keyboard စာရင်း
    keyboard = []
    for name, price in packages.items():
        keyboard.append([InlineKeyboardButton(f"{name} - {price} MMK", callback_data=name)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    return GAME_ID


# Package ရွေးပြီး Game ID တောင်း
async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_name = query.data
    user_data[update.effective_user.id] = {"package": package_name}

    await query.edit_message_text(
        f"✅ သင်ရွေးချယ်ထားတာ: {package_name}\n\n"
        "ကျေးဇူးပြုပြီး သင့် Game ID နှင့် Server ID (Zone ID) ကို ပေးပို့ပါ\n"
        "ဥပမာ 👉 12345678 (9012)"
    )
    return PAYMENT_CONFIRMATION


# Game ID လက်ခံပြီး ငွေလွှဲနည်းပေး
async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    game_id_full = update.message.text
    user_id = update.effective_user.id

    if user_id not in user_data:
        await update.message.reply_text("Error! /start နဲ့ ပြန်စပါဗျ")
        return ConversationHandler.END

    user_data[user_id]["game_id"] = game_id_full
    package = user_data[user_id]["package"]
    amount = packages[package]

    await update.message.reply_text(
        f"💳 ငွေပေးချေရန်\n\n"
        f"📱 WavePay Number: 09758486680\n"
        f"💸 Amount: {amount} MMK\n\n"
        "ငွေလွှဲပြီး Screenshot (သို့) Transaction ID ပေးပို့ပါ။"
    )

    return PAYMENT_CONFIRMATION


# Payment proof လက်ခံ
async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id not in user_data:
        await update.message.reply_text("Error! /start နဲ့ ပြန်စပါဗျ")
        return ConversationHandler.END

    package = user_data[user_id]["package"]
    game_id = user_data[user_id]["game_id"]

    order_text = (
        f"🆕 New Order!\n\n"
        f"👤 User: {user_id}\n"
        f"🎁 Package: {package}\n"
        f"🆔 Game ID: {game_id}\n\n"
        "📌 Proof အောက်ပါ message ထဲပါ"
    )

    # Admin ကို order details ပို့
    if update.message.photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=order_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
            ])
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=order_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
            ])
        )

    await update.message.reply_text("📌 သင့် order ကို Admin ဆီပိုပို့ပြီးပါပြီ။ ခဏစောင့်ပေးပါ။")

    return ConversationHandler.END


# Admin Accept/Reject
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    decision, target_user = query.data.split("_")
    target_user = int(target_user)

    if decision == "accept":
        await context.bot.send_message(chat_id=target_user, text="✅ သင့် Order ကို အတည်ပြုပြီး Diamonds ဖြည့်ပေးပါမယ်!")
        await query.edit_message_text("Order Accepted ✅")
        # Auto Topup API ချိတ်ချင်ရင် ဒီနေရာမှာ ချိတ်နိုင်မယ်
    else:
        await context.bot.send_message(chat_id=target_user, text="❌ သင့် Order ကို ငြင်းပယ်လိုက်ပါပြီ။ကျေးဇူးပြု၍ အစက‌နေ ပြန်စနိုင်ဖို့  /start ပြန်နှိပ်ပေးပါ။")
        await query.edit_message_text("Order Rejected ❌")


# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Order ကို ဖျက်လိုက်ပါပြီ။ /start နဲ့ ပြန်စတင်ပါဗျ")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GAME_ID: [CallbackQueryHandler(select_package)],
            PAYMENT_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id),
                MessageHandler(filters.PHOTO, receive_payment_proof)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(accept|reject)_"))

    app.run_polling()


if __name__ == "__main__":
    main()
