import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد سجل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key الخاص بـ Smartcat
SMARTCAT_API_KEY = "2_FwEmd5QMpKxDbHnNnwydzEL3o"
SMARTCAT_API_ENDPOINT = "https://api.smartcat.ai/api2/v2/translate"

# دالة ترجمة ملف PDF باستخدام Smartcat API
def translate_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        files = {'file': pdf_file}
        data = {'source_language': 'en', 'target_language': 'ar'}
        headers = {'Authorization': f"Bearer {SMARTCAT_API_KEY}"}

        try:
            response = requests.post(SMARTCAT_API_ENDPOINT, files=files, data=data, headers=headers)
            if response.status_code == 200:
                return response.content  # الملف المترجم
            else:
                logger.error("فشل الترجمة. الكود: %s، الرد: %s", response.status_code, response.text)
                return None
        except Exception as e:
            logger.error("خطأ أثناء الاتصال بـ Smartcat API: %s", str(e))
            return None

# دالة بدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحبًا! أرسل لي ملف PDF لترجمته من الإنجليزية إلى العربية.")

# دالة معالجة الملفات المرسلة
def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    if document.mime_type != 'application/pdf':
        update.message.reply_text("يرجى إرسال ملف بصيغة PDF فقط.")
        return

    file_id = document.file_id
    new_file = context.bot.get_file(file_id)

    # حفظ الملف في مجلد "downloads"
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", document.file_name)
    new_file.download(file_path)

    update.message.reply_text("جاري معالجة الملف...")

    # ترجمة الملف عبر Smartcat API
    translated_content = translate_pdf(file_path)
    if translated_content:
        translated_file_path = file_path.replace('.pdf', '.docx')
        with open(translated_file_path, 'wb') as f:
            f.write(translated_content)

        update.message.reply_text("تمت الترجمة بنجاح! إليك الملف:")
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(translated_file_path, 'rb'))
    else:
        update.message.reply_text("حدث خطأ أثناء الترجمة. يرجى المحاولة لاحقًا.")

# تشغيل البوت
def main():
    TELEGRAM_BOT_TOKEN = "5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc"  # استبدل هذا بالتوكن الفعلي
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
