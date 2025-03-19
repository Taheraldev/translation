import logging
import os
import tempfile
import subprocess
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from docx import Document
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# إعدادات معالجة النص العربي
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

def set_docx_rtl(paragraph):
    """ضبط إعدادات RTL للفقرة"""
    p_pr = paragraph._element.get_or_add_pPr()
    
    # إعداد محاذاة لليمين
    p_pr.append(OxmlElement('w:jc'))
    p_pr.jc.val = 'right'
    
    # إعداد اتجاه النص
    bidi = OxmlElement('w:bidi')
    p_pr.append(bidi)

def translate_docx(input_path, output_path):
    """ترجمة ملف DOCX مع إعدادات PDF صحيحة"""
    doc = Document(input_path)
    
    # إعداد الخط الافتراضي للمستند
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
    
    # معالجة الفقرات
    for para in doc.paragraphs:
        if para.text.strip():
            try:
                translated = translator.translate(para.text, src='en', dest='ar').text
                processed_text = fix_arabic(translated)
                
                para.clear()
                run = para.add_run(processed_text)
                run.font.name = 'Arial'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
                
                set_docx_rtl(para)
                para.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                
            except Exception as e:
                logger.error(f"DOCX Error: {e}")
    
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
                            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
                            
                            set_docx_rtl(para)
                            para.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                            
                        except Exception as e:
                            logger.error(f"Table Error: {e}")
    
    doc.save(output_path)

def translate_pptx(input_path, output_path):
    """ترجمة ملف PPTX مع إعدادات صحيحة"""
    prs = Presentation(input_path)
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame"):
                for paragraph in shape.text_frame.paragraphs:
                    if paragraph.text.strip():
                        try:
                            translated = translator.translate(paragraph.text, src='en', dest='ar').text
                            processed_text = fix_arabic(translated)
                            
                            # مسح المحتوى القديم
                            for run in paragraph.runs:
                                run.text = ''
                            
                            # إضافة النص الجديد
                            new_run = paragraph.add_run()
                            new_run.text = processed_text
                            new_run.font.name = 'Arial'
                            
                            # إعداد المحاذاة
                            paragraph.alignment = PP_ALIGN.RIGHT
                            
                        except Exception as e:
                            logger.error(f"PPTX Error: {e}")
    
    prs.save(output_path)

def convert_to_pdf(input_path, output_path):
    """تحويل DOCX إلى PDF باستخدام LibreOffice"""
    try:
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', os.path.dirname(output_path),
            input_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"LibreOffice Error: {result.stderr}")
            return False
            
        return os.path.exists(output_path)
    
    except Exception as e:
        logger.error(f"Conversion Error: {e}")
        return False

def handle_document(update: Update, context):
    document = update.message.document
    file_name = document.file_name.lower()
    
    if not (file_name.endswith('.docx') or file_name.endswith('.pptx')):
        update.message.reply_text("❌ يرجى إرسال ملف DOCX أو PPTX فقط")
        return
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, document.file_name)
        output_path = os.path.join(tmp_dir, f"translated_{document.file_name}")
        pdf_path = os.path.join(tmp_dir, "output.pdf")
        
        # تنزيل الملف
        document.get_file().download(custom_path=input_path)
        
        try:
            if file_name.endswith('.docx'):
                # ترجمة الملف
                translate_docx(input_path, output_path)
                
                # تحويل إلى PDF
                if convert_to_pdf(output_path, pdf_path):
                    update.message.reply_document(document=open(pdf_path, 'rb'), caption="PDF المترجم")
                else:
                    update.message.reply_text("❌ فشل في تحويل الملف إلى PDF")
                
                # إرسال DOCX المترجم
                update.message.reply_document(document=open(output_path, 'rb'), caption="DOCX المترجم")
                
            else:
                translate_pptx(input_path, output_path)
                update.message.reply_document(document=open(output_path, 'rb'), caption="PPTX المترجم")
            
        except Exception as e:
            logger.error(f"Processing Error: {str(e)}")
            update.message.reply_text("❌ حدث خطأ أثناء المعالجة")

def start(update: Update, context):
    update.message.reply_text(
        "مرحبًا! أرسل ملف DOCX أو PPTX للترجمة\n"
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
