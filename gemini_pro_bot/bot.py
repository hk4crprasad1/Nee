import os
import asyncio
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext
)
from dotenv import load_dotenv

from gemini_pro_bot.filters import AuthorizedUserFilter
from gemini_pro_bot.handlers import (
    start,
    help_command,
    newchat_command,
    handle_message,
    handle_image,
    handle_voice,
    handle_feedback_button,
    broadcast_message,
    get_message_type,
    broadcast_cancel,
    broadcast_start,
    BROADCAST_MESSAGE,
    MESSAGE_TYPE,
    main
)

load_dotenv()

# Database connection
DATABASE_FILE = 'user_database.db'

# Add this dictionary to store the user join status
user_join_status = {}


async def init_db():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE
            )
        ''')
        await db.commit()

WAITING_FOR_JOIN = 1

async def check_channel_membership(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    channel_id = -1002054833510  # Replace with your channel ID
    
    userids = await main()
    if user_id in userids:
        await start(update, context)
    else:
        keyboard = [
                [InlineKeyboardButton("Join Channel", url='https://t.me/+_hkGTH_Z2B02OWE9')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("To use the bot, please join our channel.", reply_markup=reply_markup)
        
    return ConversationHandler.END

async def wait_for_join(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    channel_id = -1002102707069  # Replace with your channel ID
    try:
        # Recheck user membership after waiting
        chat_member = await context.bot.get_chat_member(channel_id, user_id)
        if chat_member.status == 'member' or chat_member.status == 'administrator':
            # User joined during the waiting period, allow them to use the bot
            await start(update, context)
        else:
            # User still hasn't joined, do not respond
            pass
    except Exception as e:
        print(f"Error checking channel membership: {e}")

    return ConversationHandler.END

# In your start_bot function, add the following line to register the conversation handler
broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler('broadcast', broadcast_start)],
    states={
        BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, get_message_type)],
        MESSAGE_TYPE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_message)],
    },
    fallbacks=[CommandHandler('cancel', broadcast_cancel)]
)

def start_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", check_channel_membership))
    application.add_handler(CommandHandler("help", help_command, filters=AuthorizedUserFilter()))
    application.add_handler(CommandHandler("new", newchat_command, filters=AuthorizedUserFilter()))
    application.add_handler(broadcast_handler)

    # Any text message is sent to LLM to generate a response (only if joined)
    application.add_handler(MessageHandler(AuthorizedUserFilter() & ~filters.COMMAND & filters.TEXT, handle_message))

    # Any image is sent to LLM to generate a response (only if joined)
    application.add_handler(MessageHandler(AuthorizedUserFilter() & ~filters.COMMAND & filters.PHOTO, handle_image))

    # Any voice message is sent to LLM to generate a response (only if joined)
    application.add_handler(MessageHandler(AuthorizedUserFilter() & ~filters.COMMAND & filters.VOICE, handle_voice))

    # Initialize the database when the bot starts
    asyncio.get_event_loop().run_until_complete(init_db())

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
