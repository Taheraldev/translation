import logging
import os
import requests
import zipfile
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from docx import Document
from pptx import Presentation
from shutil import copyfile
from pathlib import Path

# إعداد تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# رابط واجهة API لـ LibreTranslate
LIBRE_TRANSLATE_URL = "https://libretranslate-production-0e9e.up.railway.app/translate"

def translate_text(text: str, source: str = "en", target: str = "ar") -> str:
    """
    إرسال النص إلى LibreTranslate API وترجمته.
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
    استخراج النص من ملف DOCX وحفظ الصور داخل المجلد.
    """
    doc = Document(file_path)
    full_text = []
    
    # استخراج النص
    for para in doc.paragraphs:
        full_text.append(para.text)
    
    # استخراج الصور
    docx_zip = zipfile.ZipFile(file_path, 'r')
    image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
    
    images = []
    for image_file in image_files:
        image_data = docx_zip.read(image_file)
        image_name = os.path.basename(image_file)
        image_path = os.path.join("downloads", image_name)
        with open(image_path, 'wb') as img_file:
            img_file.write(image_data)
        images.append(image_path)
    
    return "\n".join(full_text), images

def create_translated_docx_with_images(translated_text: str, image_paths: list, output_path: str):
    """
    إنشاء ملف DOCX جديد يحتوي على النص المترجم والصور.
    """
    doc = Document()
    for paragraph in translated_text.split("\n"):
        doc.add_paragraph(paragraph)
    
    # إضافة الصور
    for image_path in image_paths:
        doc.add_paragraph().add_run().add_picture(image_path)
    
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
    """
    prs = Presentation(original_path)
    translated_lines = translated_text.split("\n")
    idx = 0
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip() != "" and idx < len(translated_lines):
                shape.text = translated_lines[idx]
                idx += 1
    prs.save(output_path)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("مرحباً! أرسل لي ملف .docx أو .pptx للترجمة من الإنجليزية إلى العربية.")

async def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    file_name = file.file_name
    file_id = file.file_id

    # تحميل الملف
    new_file = await context.bot.get_file(file_id)
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)
    await new_file.download_to_drive(file_path)
    logger.info("تم تحميل الملف إلى %s", file_path)

    if file_name.endswith(".docx"):
        text, images = process_docx(file_path)
        translated = translate_text(text)
        output_path = os.path.join("downloads", "translated_" + file_name)
        create_translated_docx_with_images(translated, images, output_path)
        await update.message.reply_document(document=open(output_path, "rb"))
    elif file_name.endswith(".pptx"):
        text = process_pptx(file_path)
        translated = translate_text(text)
        output_path = os.path.join("downloads", "translated_" + file_name)
        create_translated_pptx(file_path, translated, output_path)
        await update.message.reply_document(document=open(output_path, "rb"))
    else:
        await update.message.reply_text("نوع الملف غير مدعوم. يرجى إرسال ملف بصيغة .docx أو .pptx.")

def main() -> None:
    # ضع هنا توكن بوت التليجرام الخاص بك
    TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"
    
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == '__main__':
    main()
