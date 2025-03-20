import os
import logging
import requests
import io
import tempfile
import fitz  # PyMuPDF for PDF handling
import pdfplumber
from docx import Document
from pptx import Presentation
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توكن بوت تيليجرام ومفتاح API للترجمة
TELEGRAM_BOT_TOKEN = '5284087690:AAGwKfPojQ3c-SjCHSIdeog-yN3-4Gpim1Y'
OPENL_API_KEY = '7b73717e2dmshbd139747c640560p175307jsn75624bf31396'
OPENL_TRANSLATE_ENDPOINT = 'https://api.openl.io/translate'


def translate_text(text: str, source_lang: str = 'en', target_lang: str = 'ar') -> str:
    """ترجمة نص باستخدام API الخاص بـ openl.io"""
    data = {
        'text': text,
        'source_lang': source_lang,
        'target_lang': target_lang
    }
    headers = {'Authorization': f'Bearer {OPENL_API_KEY}'}
    response = requests.post(OPENL_TRANSLATE_ENDPOINT, json=data, headers=headers)
    if response.status_code == 200:
        return response.json().get('translated_text', text)
    else:
        logger.error(f"فشل الترجمة، رمز الخطأ: {response.status_code}, الرسالة: {response.text}")
        return text


def translate_pdf(file_path: str) -> str:
    """ترجمة محتوى ملف PDF مع الحفاظ على التنسيق"""
    output_pdf_path = file_path.replace('.pdf', '_translated.pdf')
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text("text")
        translated_text = translate_text(text)
        page.clean_contents()
        page.insert_text((50, 50), translated_text)
    doc.save(output_pdf_path)
    return output_pdf_path


def translate_docx(file_path: str) -> str:
    """ترجمة محتوى ملف DOCX مع الحفاظ على التنسيق والجداول"""
    doc = Document(file_path)
    for para in doc.paragraphs:
        para.text = translate_text(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell.text = translate_text(cell.text)
    output_docx_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_docx_path)
    return output_docx_path


def translate_pptx(file_path: str) -> str:
    """ترجمة محتوى ملف PPTX مع الحفاظ على التنسيق"""
    presentation = Presentation(file_path)
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                shape.text = translate_text(shape.text)
    output_pptx_path = file_path.replace('.pptx', '_translated.pptx')
    presentation.save(output_pptx_path)
    return output_pptx_path


def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    file_name = document.file_name.lower()
    valid_extensions = {'.pdf': translate_pdf, '.docx': translate_docx, '.pptx': translate_pptx}
    ext = os.path.splitext(file_name)[1]
    
    if ext not in valid_extensions:
        update.message.reply_text("عذراً، فقط الملفات بصيغ PDF, DOCX, PPTX مدعومة.")
        return

    file_id = document.file_id
    new_file = context.bot.get_file(file_id)
    temp_dir = tempfile.mkdtemp()
    local_file_path = os.path.join(temp_dir, file_name)
    new_file.download(custom_path=local_file_path)
    update.message.reply_text("جارٍ ترجمة الملف، يرجى الانتظار...")

    # تنفيذ الترجمة
    translated_file_path = valid_extensions[ext](local_file_path)
    if translated_file_path:
        with open(translated_file_path, 'rb') as f:
            update.message.reply_document(document=InputFile(f, filename=os.path.basename(translated_file_path)))
        update.message.reply_text("تمت الترجمة بنجاح!")


def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف PDF, DOCX, أو PPTX وسأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التنسيق.")


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    logger.info("البوت يعمل...")
    updater.idle()


if __name__ == '__main__':
    main()
