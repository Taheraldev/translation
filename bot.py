import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from docx import Document
from docx.oxml.ns import qn
from pptx import Presentation

# إعدادات البوت
TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"
LIBRE_TRANSLATE_URL = "https://libretranslate-production-0e9e.up.railway.app/translate"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل لي ملف .docx أو .pptx وسأقوم بترجمته من الإنجليزية إلى العربية مع الحفاظ على التنسيق.")

def translate_text(text: str) -> str:
    """ترجمة النص مع معالجة الأخطاء"""
    if not text.strip():
        return text
    
    try:
        payload = {
            "q": text,
            "source": "en",
            "target": "ar",
            "format": "text"
        }
        response = requests.post(LIBRE_TRANSLATE_URL, json=payload, timeout=30)
        return response.json().get('translatedText', text)
    except Exception as e:
        print(f"Translation Error: {str(e)}")
        return text

def set_arabic_font(doc):
    """تحديد الخط العربي المناسب"""
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')

def process_docx(file_path: str) -> str:
    """معالجة ملفات الوورد مع الهيدر والفوتر"""
    doc = Document(file_path)
    set_arabic_font(doc)

    # معالجة الهيدر والفوتر
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            translate_paragraph(paragraph)
        for paragraph in section.footer.paragraphs:
            translate_paragraph(paragraph)

    # معالجة الفقرات الرئيسية
    for paragraph in doc.paragraphs:
        translate_paragraph(paragraph)

    # معالجة الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    translate_paragraph(paragraph)

    new_path = file_path.replace(".docx", "_translated.docx")
    doc.save(new_path)
    return new_path

def translate_paragraph(paragraph):
    """ترجمة فقرة مع الحفاظ على التنسيق"""
    original_runs = [run.text for run in paragraph.runs]
    translated_text = translate_text(paragraph.text)
    
    paragraph.clear()
    new_run = paragraph.add_run(translated_text)
    
    # الحفاظ على تنسيق الخط الأساسي
    if paragraph.runs:
        original_format = paragraph.runs[0].font
        new_run.font.name = original_format.name
        new_run.font.size = original_format.size

def process_pptx(file_path: str) -> str:
    """معالجة ملفات الباوربوينت مع الجداول والأشكال"""
    prs = Presentation(file_path)
    
    for slide in prs.slides:
        for shape in slide.shapes:
            # معالجة النصوص في الأشكال
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.text = translate_text(run.text)
            
            # معالجة الجداول
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.text = translate_text(run.text)
    
    new_path = file_path.replace(".pptx", "_translated.pptx")
    prs.save(new_path)
    return new_path

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملفات المستقبلة"""
    try:
        file = await update.message.effective_attachment.get_file()
        file_name = update.message.effective_attachment.file_name
        await file.download_to_drive(file_name)
        
        await update.message.reply_text("⏳ جاري الترجمة... قد يستغرق الأمر بضع دقائق")
        
        if file_name.endswith('.docx'):
            output_path = process_docx(file_name)
        elif file_name.endswith('.pptx'):
            output_path = process_pptx(file_name)
        else:
            await update.message.reply_text("❌ نوع الملف غير مدعوم!")
            return

        await update.message.reply_document(document=open(output_path, 'rb'))
        
        # التنظيف
        os.remove(file_name)
        os.remove(output_path)
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("Bot is running...")
    app.run_polling()
