import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Configuration Variables
BOT_TOKEN = "8515239358:AAEfIuELaFQMBCXZC0nUzP6StjTmNwowBxE"
ADMIN_CHAT_ID = 8951384051

# Conversation States
CHOOSING_CATEGORY, ENTERING_DESCRIPTION, ATTACHING_MEDIA, CONFIRMATION = range(4)

# 1. /start Command
def start(update: Update, context: CallbackContext) -> int:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 **ආයුබෝවන් {user_name}!**\n\n"
        "✨ **Bug Reporter Bot** වෙත සාදරයෙන් පිළිගනිමු!\n\n"
        "⚡ *ඔබ මුහුණ දුන් තාක්ෂණික ගැටලුව හෝ Bug එක අප වෙත යොමු කිරීමට පහත Button එක ක්ලික් කරන්න.*"
    )
    keyboard = [
        [InlineKeyboardButton("🐛 Report a Bug", callback_data="report_bug")],
        [InlineKeyboardButton("ℹ️ Help & Info", callback_data="help_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        query = update.callback_query
        query.answer()
        query.edit_message_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return CHOOSING_CATEGORY

# Category Selection
def select_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == "help_info":
        info_text = (
            "🛠 **භාවිත කරන ආකාරය:**\n\n"
            "1️⃣ Bug Category එක තෝරන්න.\n"
            "2️⃣ ගැටලුව පිළිබඳ විස්තරයක් ඇතුළත් කරන්න.\n"
            "3️⃣ අවශ්‍ය නම් Screenshot එකක් යවන්න.\n\n"
            "💡 *අපගේ Developer කණ්ඩායම ඉක්මනින් එය පරීක්ෂා කරනු ඇත!*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")]]
        query.edit_message_text(info_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSING_CATEGORY

    category_text = "📂 **කරුණාකර Bug එකට අදාළ Category එක තෝරන්න:**"
    keyboard = [
        [InlineKeyboardButton("📱 UI / Layout Issue", callback_data="cat_ui")],
        [InlineKeyboardButton("⚠️ System Crash / Error", callback_data="cat_crash")],
        [InlineKeyboardButton("🌐 Network / Connection", callback_data="cat_net")],
        [InlineKeyboardButton("⚙️ Other Issue", callback_data="cat_other")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    query.edit_message_text(category_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    return ENTERING_DESCRIPTION

# Description Entry
def get_description(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == "cancel":
        return cancel(update, context)
        
    category_map = {
        "cat_ui": "UI / Layout Issue",
        "cat_crash": "System Crash / Error",
        "cat_net": "Network / Connection",
        "cat_other": "Other Issue"
    }
    context.user_data['category'] = category_map.get(query.data, "General")
    
    msg_text = (
        f"📌 **Selected Category:** `{context.user_data['category']}`\n\n"
        "✍️ **දැන් ඔබට මුහුණ පෑමට සිදු වූ Bug එක පිළිබඳ විස්තරය ටයිප් කර යවන්න:**"
    )
    query.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN)
    return ATTACHING_MEDIA

# Media or Skip Step
def get_media(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    
    media_text = (
        "📸 **Screenshot එකක් ඇමුණුමට එක් කිරීමට අවශ්‍යද?**\n\n"
        "කරුණාකර Screenshot එකක් Photo එකක් ලෙස Send කරන්න. නැතහොත් **Skip** Button එක ක්ලික් කරන්න."
    )
    keyboard = [
        [InlineKeyboardButton("⏩ Skip Screenshot", callback_data="skip_media")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    update.message.reply_text(media_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

# Final Submission
def process_submission(update: Update, context: CallbackContext) -> int:
    query = update.callback_query if update.callback_query else None
    
    if query:
        query.answer()
        if query.data == "skip_media":
            context.user_data['photo'] = None
    elif update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id

    status_msg = None
    if query:
        status_msg = query.edit_message_text("🔄 *Sending Bug Report... 25%*", parse_mode=ParseMode.MARKDOWN)
    else:
        status_msg = update.message.reply_text("🔄 *Sending Bug Report... 25%*", parse_mode=ParseMode.MARKDOWN)

    user = update.effective_user
    admin_text = (
        "🚨 **NEW BUG REPORT RECEIVED** 🚨\n\n"
        f"👤 **User:** [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n"
        f"📂 **Category:** `{context.user_data.get('category')}`\n\n"
        f"📝 **Description:**\n{context.user_data.get('description')}"
    )

    if context.user_data.get('photo'):
        context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=context.user_data['photo'], caption=admin_text, parse_mode=ParseMode.MARKDOWN)
    else:
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode=ParseMode.MARKDOWN)

    final_success = (
        "✅ **Bug Report එක සාර්ථකව යොමු කරන ලදී!**\n\n"
        "✨ *අපගේ Technical Team එක මඟින් මෙය පරීක්ෂා කර බලා ඉදිරි පියවර ගනු ඇත. ස්තූතියි!*"
    )
    keyboard = [[InlineKeyboardButton("🔄 Send Another Report", callback_data="back_main")]]
    
    context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
        text=final_success,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_CATEGORY

# Cancel Handler
def cancel(update: Update, context: CallbackContext) -> int:
    text = "❌ **ක්‍‍රියාවලිය අවලංගු කරන ලදී.**"
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]]
    if update.callback_query:
        update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CATEGORY

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(start, pattern="^back_main$")
        ],
        states={
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(select_category, pattern="^(report_bug|help_info)$"),
            ],
            ENTERING_DESCRIPTION: [
                CallbackQueryHandler(get_description, pattern="^cat_"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            ATTACHING_MEDIA: [
                MessageHandler(Filters.text & ~Filters.command, get_media)
            ],
            CONFIRMATION: [
                CallbackQueryHandler(process_submission, pattern="^skip_media$"),
                MessageHandler(Filters.photo, process_submission),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    print("Bot runs successfully!")
    updater.idle()

if __name__ == '__main__':
    main()
