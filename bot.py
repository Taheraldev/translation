import logging
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from docx import Document
from pptx import Presentation

# إعداد تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# رابط واجهة API لـ LibreTranslate
LIBRE_TRANSLATE_URL = "https://libretranslate.com/translate"

def translate_text(text: str, source: str = "en", target: str = "ar") -> str:
    """
    تستخدم هذه الدالة لإرسال النص إلى LibreTranslate API وترجمة النص.
    """
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    try:
        response = requests.post(LIBRE_TRANSLATE_URL, data=payload)
        if response.status_code == 200:
            result = response.json()
            return result["translatedText"]
        else:
            logger.error("خطأ في الترجمة: %s", response.text)
            return text
    except Exception as e:
        logger.error("استثناء أثناء الترجمة: %s", e)
        return text

def process_docx(file_path: str) -> str:
    """
    استخراج النص من ملف DOCX.
    """
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def create_translated_docx(translated_text: str, output_path: str):
    """
    إنشاء ملف DOCX جديد يحتوي على النص المترجم.
    """
    doc = Document()
    for paragraph in translated_text.split("\n"):
        doc.add_paragraph(paragraph)
    doc.save(output_path)

def process_pptx(file_path: str) -> str:
    """
    استخراج النص من ملف PPTX.
    """
    prs = Presentation(file_path)
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
    return "\n".join(texts)

def create_translated_pptx(original_path: str, translated_text: str, output_path: str):
    """
    إنشاء ملف PPTX جديد مع النصوص المترجمة.
    يُلاحظ أن هذه العملية تقديرية، حيث نحاول استبدال النصوص في الشرائح بالنص المترجم.
    """
    prs = Presentation(original_path)
    # تقسيم النص المترجم بناءً على عدد الأسطر (هذه الطريقة تقريبية وقد تحتاج لضبط)
    translated_lines = translated_text.split("\n")
    idx = 0
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip() != "" and idx < len(translated_lines):
                shape.text = translated_lines[idx]
                idx += 1
    prs.save(output_path)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("مرحباً! أرسل لي ملف (.docx أو .pptx) للترجمة من الإنجليزية إلى العربية.")

def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    file_name = file.file_name
    file_id = file.file_id

    # تحميل الملف
    new_file = context.bot.get_file(file_id)
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)
    new_file.download(custom_path=file_path)
    logger.info("تم تحميل الملف إلى %s", file_path)

    if file_name.endswith(".docx"):
        text = process_docx(file_path)
        translated = translate_text(text)
        output_path = os.path.join("downloads", "translated_" + file_name)
        create_translated_docx(translated, output_path)
        update.message.reply_document(document=open(output_path, "rb"))
    elif file_name.endswith(".pptx"):
        text = process_pptx(file_path)
        translated = translate_text(text)
        output_path = os.path.join("downloads", "translated_" + file_name)
        create_translated_pptx(file_path, translated, output_path)
        update.message.reply_document(document=open(output_path, "rb"))
    else:
        update.message.reply_text("نوع الملف غير مدعوم. يرجى إرسال ملف بصيغة .docx أو .pptx.")

def main() -> None:
    # ضع هنا توكن بوت التليجرام الخاص بك
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
