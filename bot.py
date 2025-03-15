import os
import requests
import tempfile
from telegram import Bot, Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد توكن البوت ومفتاح API الخاص بـ Apify
TELEGRAM_BOT_TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"
APIFY_API_KEY = "apify_api_f3RTo40c6qrsfZmg9Fw4fIvkZgpgU50ausCM"
APIFY_TRANSLATION_API = "https://api.apify.com/v2/actor-runs?token=" + APIFY_API_KEY

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحبًا! أرسل ملف PDF لترجمته من الإنجليزية إلى العربية.")

def translate_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    if document.mime_type != "application/pdf":
        update.message.reply_text("يرجى إرسال ملف PDF فقط.")
        return
    
    # تنزيل الملف مؤقتًا
    file = context.bot.get_file(document.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        file.download(temp_pdf.name)
        pdf_path = temp_pdf.name
    
    update.message.reply_text("جارٍ رفع الملف للترجمة... هذا قد يستغرق بعض الوقت.")
    
    # رفع الملف إلى Apify
    with open(pdf_path, "rb") as pdf_file:
        response = requests.post(
            APIFY_TRANSLATION_API,
            files={"file": pdf_file},
            data={"language": "en", "target_language": "ar"}
        )
    
    if response.status_code != 200:
        update.message.reply_text("حدث خطأ أثناء رفع الملف إلى Apify.")
        os.remove(pdf_path)
        return
    
    # انتظار الترجمة واستلام الملف المترجم
    result = response.json()
    translated_pdf_url = result.get("translated_pdf_url")
    if not translated_pdf_url:
        update.message.reply_text("لم يتم العثور على الملف المترجم.")
        os.remove(pdf_path)
        return
    
    # تنزيل الملف المترجم
    translated_pdf_path = pdf_path.replace(".pdf", "_translated.pdf")
    with requests.get(translated_pdf_url, stream=True) as r:
        with open(translated_pdf_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    
    # إرسال الملف المترجم إلى المستخدم
    update.message.reply_document(document=InputFile(translated_pdf_path), filename="translated.pdf")
    
    # تنظيف الملفات المؤقتة
    os.remove(pdf_path)
    os.remove(translated_pdf_path)

# إعداد البوت
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), translate_pdf))

# تشغيل البوت
print("البوت يعمل...")
updater.start_polling()
updater.idle()
