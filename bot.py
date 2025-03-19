import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد سجل الأخطاء (يمكنك تعديل الإعدادات حسب الحاجة)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key الخاص بـ Smartcat
SMARTCAT_API_KEY = "2_FwEmd5QMpKxDbHnNnwydzEL3o"
# رابط نهاية API لـ Smartcat (يرجى التأكد من الوثائق وتحديث الرابط إذا لزم الأمر)
SMARTCAT_API_ENDPOINT = "https://api.smartcat.ai/api2/v2/translate"  # مثال، قم بالتعديل حسب التوثيق

# دالة لترجمة ملف PDF باستخدام Smartcat API
def translate_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        files = {'file': pdf_file}
        # إعداد المعلمات اللازمة للترجمة:
        data = {
            'source_language': 'en',  # اللغة المصدر: الإنجليزية
            'target_language': 'ar',  # اللغة الهدف: العربية
            # يمكن إضافة معلمات أخرى إذا كان ذلك مطلوباً من API (مثلاً نوع التحويل أو التنسيقات)
        }
        headers = {
            'Authorization': f"Bearer {SMARTCAT_API_KEY}"
        }
        try:
            response = requests.post(SMARTCAT_API_ENDPOINT, files=files, data=data, headers=headers)
            if response.status_code == 200:
                # يفترض أن يكون الرد هو الملف المترجم بصيغة docx
                return response.content
            else:
                logger.error("فشل الترجمة. الكود: %s، الرد: %s", response.status_code, response.text)
                return None
        except Exception as e:
            logger.error("استثناء أثناء الاتصال بـ Smartcat API: %s", str(e))
            return None

# دالة بدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف PDF للترجمة من الإنجليزية إلى العربية.")

# دالة التعامل مع الملفات المرسلة من المستخدم
def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    # التحقق من أن الملف بصيغة PDF
    if document.mime_type != 'application/pdf':
        update.message.reply_text("يرجى إرسال ملف بصيغة PDF فقط.")
        return

    # تحميل الملف من تيليجرام
    file_id = document.file_id
    new_file = context.bot.get_file(file_id)
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", document.file_name)
    new_file.download(file_path)
    update.message.reply_text("جاري معالجة الملف...")

    # ترجمة الملف باستخدام Smartcat API
    translated_content = translate_pdf(file_path)
    if translated_content:
        # حفظ الملف المترجم بصيغة DOCX
        translated_file_path = file_path.replace('.pdf', '.docx')
        with open(translated_file_path, 'wb') as f:
            f.write(translated_content)
        update.message.reply_text("تمت الترجمة بنجاح. إليك الملف:")
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(translated_file_path, 'rb'))
    else:
        update.message.reply_text("حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى لاحقاً.")

def main():
    # ضع توكن بوت تيليجرام الخاص بك هنا
    TELEGRAM_BOT_TOKEN = "5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc"  # استبدله بالتوكن الفعلي
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # إضافة المعالجات (Handlers)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_document))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
