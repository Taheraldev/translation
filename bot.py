import logging
import os
import requests
import docx
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات API الخاصة بموقع otranslator.com
API_KEY = "sk-32292721afeabc8a1f984e62dbc7f726aeab6e7c7b1547d0e1161f169971"
TRANSLATION_ENDPOINT = "https://otranslator.com/api/v1/translate"  # تأكد من صحة الرابط حسب التوثيق

# رمز بوت تلغرام (قم بتعديله)
TELEGRAM_BOT_TOKEN = "6016945663:AAHjacRdRfZ2vUgS2SLmoFgHfMdUye4l6bA"

# إعداد سجل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل ملف DOCX وسأقوم بترجمته من الإنجليزية إلى العربية.")

def translate_text(text: str) -> str:
    """
    الدالة ترسل النص إلى API الترجمة وتعيد النص المترجم.
    تأكد من مطابقة المتغيرات حسب التوثيق الخاص بـ otranslator.com.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "source_language": "en",
        "target_language": "ar"
    }
    try:
        response = requests.post(TRANSLATION_ENDPOINT, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("translated_text", "")
        else:
            logger.error(f"خطأ في API الترجمة: {response.status_code} {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Exception during translation: {e}")
        return ""

def process_docx(file_path: str) -> str:
    """
    استخراج النص من ملف DOCX.
    """
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def create_docx(text: str, output_path: str):
    """
    إنشاء ملف DOCX جديد يحتوي على النص المُترجم.
    """
    doc = docx.Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(output_path)

def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    if document.file_name.lower().endswith(".docx"):
        # تحميل الملف
        file = document.get_file()
        os.makedirs("downloads", exist_ok=True)
        file_path = os.path.join("downloads", document.file_name)
        file.download(custom_path=file_path)
        update.message.reply_text("تم استلام الملف. جاري عملية الترجمة...")

        # استخراج النص من الملف
        original_text = process_docx(file_path)
        if not original_text.strip():
            update.message.reply_text("لا يمكن استخراج نص من الملف المرسل.")
            return

        # ترجمة النص
        translated_text = translate_text(original_text)
        if not translated_text:
            update.message.reply_text("حدث خطأ أثناء الترجمة.")
            return

        # إنشاء ملف DOCX جديد بالنص المترجم
        output_file = os.path.join("downloads", "translated_" + document.file_name)
        create_docx(translated_text, output_file)

        # إرسال الملف المترجم إلى المستخدم
        update.message.reply_document(document=open(output_file, "rb"))
    else:
        update.message.reply_text("يرجى إرسال ملف بصيغة DOCX فقط.")

def main():
    # إعداد بوت تلغرام
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # إعداد المعالجات
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    # بدء البوت
    updater.start_polling()
    logger.info("البوت يعمل الآن...")
    updater.idle()

if __name__ == '__main__':
    main()
