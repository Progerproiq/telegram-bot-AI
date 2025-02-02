from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import openai
import asyncio
import os
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()


# Ініціалізація OpenAI API
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Константи для кнопок
CONSULTATION_TEXT = "Замовити консультацію Дьомена Андрія"
PAYMENT_TEXT = "Оплата послуг"
CALL_LAWYER_TEXT = "Набрати Адвоката на телефон"
MESSAGE_LAWYER_TEXT = "Написати адвокату повідомлення на телеграм"
MAIN_MENU_TEXT = "Повернення до головного меню"

# Ідентифікатор групи для пересилання повідомлень
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# Функція для команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_ai_question"] = False  # Скидання стану AI запитів
    keyboard_reply = [[CONSULTATION_TEXT, PAYMENT_TEXT]]
    reply_markup = ReplyKeyboardMarkup(keyboard_reply, resize_keyboard=True)

    keyboard_inline = [
        [InlineKeyboardButton("Веб сайт", url="https://notguilty.dp.ua/")],
        [InlineKeyboardButton("Допомога Юридичного штучного інтелекту", callback_data="ai_help")]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard_inline)

    await update.message.reply_text(
        'Привіт! Я готовий допомогти вам. Для отримання допомоги переходьте на наш сайт, задайте ваше запитання АІ або Адвокату.',
        reply_markup=inline_markup
    )
    await update.message.reply_text(
        'Виберіть одну з кнопок нижче або вище для подальших дій.',
        reply_markup=reply_markup
    )

# Функція для консультацій
async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    consultation_text = (
        "Онлайн консультація! ✅\n\n"
        "Ціна - 3000 грн\n"
        "Тривалість - 60 хв\n\n"
        "Формат - по телефону чи відеозв'язку.\n"
        "Робочі години Пн-Пт: 10:00-20:00 Cб-Нд: 10:00-15:00.\n\n"
        "Для отримання консультації ⬇️\n"
        "1. Напишіть ПІБ\n"
        "2. Номер телефону\n"
        "3. Короткий опис вашого питання"
    )

    keyboard_reply = [
        [CALL_LAWYER_TEXT, MESSAGE_LAWYER_TEXT],
        [MAIN_MENU_TEXT]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_reply, resize_keyboard=True)

    await update.message.reply_text(consultation_text, reply_markup=reply_markup)

# Функція для оплати
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Скопіюйте номер натиснувши на нього: \n`8888 8888 8888 8888`",
        parse_mode="Markdown"
    )

# Функція для дзвінка адвокату
async def call_lawyer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Скопіюйте номер натиснувши на нього:\n`+380888888888`",
        parse_mode="Markdown"
    )

# Функція для написання адвокату у Telegram
async def message_lawyer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard_inline = [[InlineKeyboardButton("Написати адвокату", url="https://t.me/Pro8883")]]
    reply_markup = InlineKeyboardMarkup(keyboard_inline)
    await update.message.reply_text("Натисніть, щоб написати адвокату:", reply_markup=reply_markup)

# Функція для повернення до головного меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

# Функція обробки callback кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "ai_help":
        await query.message.reply_text(
            "Напишіть ваше юридичне питання нижче, і я допоможу вам із професійною консультацією."
        )
        context.user_data["awaiting_ai_question"] = True

# Функція для обробки запитів до AI
async def handle_ai_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("awaiting_ai_question", False):
        question = update.message.text
        response = await ask_ai_lawyer(question)
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Вибачте, але сталася помилка під час обробки вашого запиту.")
    else:
        await forward_to_group(update, context)

# Функція для запитів до OpenAI
async def ask_ai_lawyer(question: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ти — професійний адвокат, знаний як 'АІ Юрист України'. Відповідай на юридичні питання чітко, професійно, і лише у відповідності до Українського та міжнародного права."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Помилка OpenAI API: {str(e)}"

# Функція для пересилання повідомлень у групу
async def forward_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_ai_question", False):
        if update.message:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"Повідомлення від {update.message.from_user.first_name}: {update.message.text}")

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(CONSULTATION_TEXT), consultation))
    app.add_handler(MessageHandler(filters.Text(PAYMENT_TEXT), payment))
    app.add_handler(MessageHandler(filters.Text(CALL_LAWYER_TEXT), call_lawyer))
    app.add_handler(MessageHandler(filters.Text(MESSAGE_LAWYER_TEXT), message_lawyer))

    app.add_handler(MessageHandler(filters.Text(MAIN_MENU_TEXT), main_menu))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_query))

    app.run_polling()

