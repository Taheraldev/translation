import logging
import os
import tempfile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from docx import Document
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display

# إعدادات معالجة النص العربي (طريقة جديدة)
reshaper = arabic_reshaper.ArabicReshaper()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()

def fix_arabic(text):
    """معالجة النص العربي مع الحفاظ على التنسيق"""
    reshaped = reshaper.reshape(text)
    return get_display(reshaped)

def translate_docx(input_path, output_path):
    """ترجمة ملف DOCX مع الحفاظ على التنسيق"""
    doc = Document(input_path)
    
    # معالجة الفقرات الرئيسية
    for para in doc.paragraphs:
        if para.text.strip():
            try:
                translated = translator.translate(para.text, src='en', dest='ar').text
                processed_text = fix_arabic(translated)
                para.clear()
                run = para.add_run(processed_text)
                run.font.name = 'Arial'
            except Exception as e:
                logger.error(f"Error in DOCX translation: {e}")
    
    # معالجة الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text.strip():
                        try:
                            translated = translator.translate(para.text, src='en', dest='ar').text
                            processed_text = fix_arabic(translated)
                            para.clear()
                            run = para.add_run(processed_text)
                            run.font.name = 'Arial'
                        except Exception as e:
                            logger.error(f"Error in table translation: {e}")
    
    doc.save(output_path)

def translate_pptx(input_path, output_path):
    """ترجمة ملف PPTX مع الحفاظ على التنسيق"""
    prs = Presentation(input_path)
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame"):
                for paragraph in shape.text_frame.paragraphs:
                    if paragraph.text.strip():
                        try:
                            translated = translator.translate(paragraph.text, src='en', dest='ar').text
                            processed_text = fix_arabic(translated)
                            paragraph.text = processed_text
                            paragraph.alignment = PP_ALIGN.RIGHT
                            for run in paragraph.runs:
                                run.font.name = 'Arial'
                        except Exception as e:
                            logger.error(f"Error in PPTX translation: {e}")
    
    prs.save(output_path)

def handle_document(update: Update, context):
    """معالجة الملفات المرسلة"""
    document = update.message.document
    file_name = document.file_name.lower()
    
    if not (file_name.endswith('.docx') or file_name.endswith('.pptx')):
        update.message.reply_text("❌ يرجى إرسال ملف DOCX أو PPTX فقط")
        return
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, document.file_name)
        output_path = os.path.join(tmp_dir, f"translated_{document.file_name}")
        
        # تنزيل الملف
        document.get_file().download(custom_path=input_path)
        
        try:
            if file_name.endswith('.docx'):
                translate_docx(input_path, output_path)
            else:
                translate_pptx(input_path, output_path)
            
            # إرسال الملف المترجم
            update.message.reply_document(
                document=open(output_path, 'rb'),
                caption="✅ تمت الترجمة بنجاح"
            )
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            update.message.reply_text("❌ حدث خطأ أثناء المعالجة")

def start(update: Update, context):
    """رسالة البداية"""
    update.message.reply_text(
        "مرحبًا! أرسل ملف DOCX أو PPTX لترجمته إلى العربية\n"
        "المطور: @ta_ja199"
    )

def main():
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
