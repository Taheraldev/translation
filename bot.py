import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import os

# استبدل برموز API الخاصة بك
TELEGRAM_BOT_TOKEN = "5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc"
PDF2DOCX_API_KEY = "api_production_4fd69fa4d6a13fc2c89f09280b05babb71b8ed18da5f87bc9daa3198e0da5b03.67dd34d41b1ec0ad5910e28c.67ddb5411b1ec0ad5910eb1e"

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي ملف PDF وسأقوم بتحويله إلى DOCX.")

def handle_pdf(update, context):
    file_id = update.message.document.file_id
    file_info = context.bot.get_file(file_id)
    file_url = file_info.file_path

    # تحميل ملف PDF
    pdf_file = requests.get(file_url)
    with open("input.pdf", "wb") as f:
        f.write(pdf_file.content)

    # تحويل PDF إلى DOCX باستخدام pdf2docx API
    url = "https://pdf2docx.com/api/convert"
    files = {"file": open("input.pdf", "rb")}
    headers = {"Authorization": f"Bearer {PDF2DOCX_API_KEY}"}
    try:
        response = requests.post(url, files=files, headers=headers)

        if response.status_code == 200:
            with open("output.docx", "wb") as f:
                f.write(response.content)
            context.bot.send_document(chat_id=update.effective_chat.id, document=open("output.docx", "rb"))
            os.remove("output.docx") # حذف ملف ال docx بعد إرساله
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ أثناء التحويل. حالة الاستجابة: {response.status_code}")
    except requests.exceptions.RequestException as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ في الاتصال: {e}")

    # حذف الملف المؤقت
    os.remove("input.pdf")

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
