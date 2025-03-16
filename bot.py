import logging
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from io import BytesIO
from PyPDF2 import PdfReader
import docx
from pptx import Presentation

# إعدادات API لـ Yandex Translate
YANDEX_API_KEY = "2bbded23-5c80-4a79-8ea9-7928460acc41"
YANDEX_TRANSLATE_URL = "https://translate.yandex.net/api/v1.5/tr.json/translate"

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دالة الترجمة (من الإنجليزية إلى العربية فقط)
def translate_text(text: str) -> str:
    params = {
        "key": YANDEX_API_KEY,
        "text": text,
        "lang": "en-ar"  # الترجمة من الإنجليزية إلى العربية
    }
    try:
        response = requests.get(YANDEX_TRANSLATE_URL, params=params)
        response.raise_for_status()
        result = response.json()
        if "text" in result:
            return "\n".join(result["text"])
    except Exception as e:
        logger.error(f"Error during translation: {e}")
    return "حدث خطأ أثناء الترجمة."

# استخراج النص من ملفات PDF
def extract_text_pdf(file_bytes: BytesIO) -> str:
    try:
        reader = PdfReader(file_bytes)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return ""

# استخراج النص من ملفات DOCX
def extract_text_docx(file_bytes: BytesIO) -> str:
    try:
        document = docx.Document(file_bytes)
        text = "\n".join([para.text for para in document.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error reading DOCX: {e}")
        return ""

# استخراج النص من ملفات PPTX
def extract_text_pptx(file_bytes: BytesIO) -> str:
    try:
        prs = Presentation(file_bytes)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PPTX: {e}")
        return ""

# معالج أمر /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف (PDF, DOCX, PPTX) وسأقوم بترجمته من الإنجليزية إلى العربية باستخدام Yandex Translate API.")

# معالج استقبال الملفات
def handle_file(update: Update, context: CallbackContext):
    file = update.message.document
    if not file:
        update.message.reply_text("لم يتم العثور على ملف.")
        return

    file_name = file.file_name.lower()
    if not (file_name.endswith('.pdf') or file_name.endswith('.docx') or file_name.endswith('.pptx')):
        update.message.reply_text("صيغة الملف غير مدعومة. الرجاء إرسال ملف PDF, DOCX أو PPTX.")
        return

    # تنزيل الملف من تلغرام
    file_id = file.file_id
    new_file = context.bot.get_file(file_id)
    file_bytes = BytesIO(new_file.download_as_bytearray())

    # استخراج النص اعتمادًا على صيغة الملف
    text = ""
    if file_name.endswith('.pdf'):
        text = extract_text_pdf(file_bytes)
    elif file_name.endswith('.docx'):
        text = extract_text_docx(file_bytes)
    elif file_name.endswith('.pptx'):
        text = extract_text_pptx(file_bytes)

    if not text.strip():
        update.message.reply_text("لم أتمكن من استخراج النص من الملف.")
        return

    # ترجمة النص من الإنجليزية إلى العربية
    translated_text = translate_text(text)

    # إرسال النص المترجم (أو ملف نصي إذا كان كبيرًا)
    if len(translated_text) > 4000:
        output_file = BytesIO(translated_text.encode('utf-8'))
        output_file.name = "translated.txt"
        update.message.reply_document(document=output_file)
    else:
        update.message.reply_text(translated_text)

def main():
    # ضع هنا رمز بوت تلغرام الخاص بك
    TELEGRAM_BOT_TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
