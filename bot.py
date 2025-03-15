import os
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from docx import Document
from pptx import Presentation

# إعدادات البوت
TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"
LIBRE_TRANSLATE_URL = "https://libretranslate-production-0e9e.up.railway.app/translate"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل لي ملف .docx أو .pptx وسأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التنسيق.")

def translate_text(text):
    payload = {
        "q": text,
        "source": "en",
        "target": "ar",
        "format": "text"
    }
    response = requests.post(LIBRE_TRANSLATE_URL, json=payload)
    return response.json()['translatedText']

def process_docx(file_path):
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            translated = translate_text(paragraph.text)
            paragraph.text = translated
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    translated = translate_text(cell.text)
                    cell.text = translated
    new_path = file_path.replace(".docx", "_translated.docx")
    doc.save(new_path)
    return new_path

def process_pptx(file_path):
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                translated = translate_text(shape.text)
                shape.text = translated
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            translated = translate_text(cell.text)
                            cell.text = translated
    new_path = file_path.replace(".pptx", "_translated.pptx")
    prs.save(new_path)
    return new_path

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name
    
    # تحميل الملف
    file = await context.bot.get_file(file_id)
    await file.download_to_drive(file_name)
    
    await update.message.reply_text("جاري الترجمة... قد يستغرق بعض الوقت")
    
    try:
        if file_name.endswith('.docx'):
            output_path = process_docx(file_name)
        elif file_name.endswith('.pptx'):
            output_path = process_pptx(file_name)
        else:
            await update.message.reply_text("نوع الملف غير مدعوم! يرجى إرسال ملف .docx أو .pptx")
            return
        
        with open(output_path, 'rb') as f:
            await update.message.reply_document(f)
        
        # التنظيف: حذف الملفات المؤقتة
        os.remove(file_name)
        os.remove(output_path)
    
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء المعالجة: {str(e)}")
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    print("Bot is running...")
    application.run_polling()
