import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# تعيين التوكن من متغير البيئة
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise ValueError("❌ خطأ: لم يتم العثور على ACCESS_TOKEN. تأكد من تعيينه بشكل صحيح!")

# إعداد التوكن في الهيدرز
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}".encode("utf-8", "ignore").decode("latin-1"),
    "Accept": "application/json"
}

API_URL = "https://api.groupdocs.cloud/v2.0/translation/pdf"

# دالة الترجمة

def translate_pdf(file_path):
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {
            "sourceLanguage": "en",
            "targetLanguages": ["ar"],
            "outputFormat": "pdf"
        }
        
        response = requests.post(API_URL, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            translated_pdf_path = "translated.pdf"
            with open(translated_pdf_path, "wb") as out_file:
                out_file.write(response.content)
            return translated_pdf_path
        else:
            print("❌ خطأ أثناء الترجمة:", response.text)
            return None

# دالة استقبال الملفات

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file_path = "received.pdf"
    file.download(file_path)
    
    translated_file_path = translate_pdf(file_path)
    if translated_file_path:
        update.message.reply_document(document=open(translated_file_path, "rb"), caption="✅ تم الترجمة بنجاح!")
    else:
        update.message.reply_text("❌ حدث خطأ أثناء الترجمة.")

# تشغيل البوت

def main():
    updater = Updater("5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
