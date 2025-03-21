import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import os

# جایگزینی توکن بات تلگرام و کلید API pdf2docx
TELEGRAM_BOT_TOKEN = "5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc"
PDF2DOCX_API_KEY = "api_production_4fd69fa4d6a13fc2c89f09280b05babb71b8ed18da5f87bc9daa3198e0da5b03.67dd34d41b1ec0ad5910e28c.67ddb5411b1ec0ad5910eb1e"

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً یک فایل PDF ارسال کنید تا آن را به DOCX تبدیل کنم.")

def handle_pdf(update, context):
    file_id = update.message.document.file_id
    file_info = context.bot.get_file(file_id)
    file_url = file_info.file_path

    # دانلود فایل PDF
    pdf_file = requests.get(file_url)
    with open("input.pdf", "wb") as f:
        f.write(pdf_file.content)

    # تبدیل PDF به DOCX با استفاده از API pdf2docx
    url = "https://pdf2docx.com/api/convert"
    files = {"file": open("input.pdf", "rb")}
    headers = {"Authorization": f"Bearer {PDF2DOCX_API_KEY}"}
    response = requests.post(url, files=files, headers=headers)

    if response.status_code == 200:
        with open("output.docx", "wb") as f:
            f.write(response.content)
        context.bot.send_document(chat_id=update.effective_chat.id, document=open("output.docx", "rb"))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="متأسفانه در هنگام تبدیل خطایی رخ داد.")

    # حذف فایل‌های موقت
    os.remove("input.pdf")
    os.remove("output.docx")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    pdf_handler = MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(pdf_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
