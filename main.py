from flask import Flask
from threading import Thread

# Start dummy web server for Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Run in a separate thread
Thread(target=run).start()
﻿import json
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_1 = os.getenv("CHANNEL_1")
CHANNEL_2 = os.getenv("CHANNEL_2")

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Check user is in both channels
async def is_user_in_channels(user_id, context):
    for channel in [CHANNEL_1, CHANNEL_2]:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {"referrals": 0, "balance": 0}
        # Referral handler
        if context.args:
            ref_id = context.args[0]
            if ref_id != str(user_id) and ref_id in data:
                data[ref_id]["referrals"] += 1
                data[ref_id]["balance"] += 1
        save_data(data)

    if not await is_user_in_channels(user_id, context):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNEL_1[1:]}")],
            [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNEL_2[1:]}")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")],
        ]
        await update.message.reply_text("🚫 You must join the channels to use the bot:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Main menu
    await show_menu(update, context)

# Main menu
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    invite_link = f"https://t.me/{context.bot.username}?start={user_id}"

    buttons = [
        [InlineKeyboardButton("👥 My Referrals", callback_data="ref_info")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📖 Earning Guide", callback_data="guide")],
        [InlineKeyboardButton("🔗 Invite Link", url=invite_link)],
    ]
    await update.message.reply_text("🎉 Welcome to the Refer and Earn Bot!", reply_markup=InlineKeyboardMarkup(buttons))

# Check Join button pressed
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_user_in_channels(query.from_user.id, context):
        await query.message.edit_text("✅ You're verified! Type /start again.")
    else:
        await query.answer("❌ You still need to join both channels.", show_alert=True)

# Callback actions
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if query.data == "ref_info":
        referrals = data.get(user_id, {}).get("referrals", 0)
        balance = data.get(user_id, {}).get("balance", 0)
        text = f"👥 Referrals: {referrals}\n💰 Balance: ₹{balance}"
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "withdraw":
        text = "💸 Minimum withdrawal is ₹10.\nPlease contact admin @youradmin."
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "guide":
        text = "📖 Invite your friends using your link and earn ₹1 for each person who joins!"
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "back":
        await show_menu(update, context)

# Setup
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    print("✅ Bot running...")
    app.run_polling()
