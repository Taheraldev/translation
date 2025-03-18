import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import docx
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import arabic_reshaper
from bidi.algorithm import get_display

# إعدادات معالجة النص العربي
reshaper = arabic_reshaper.ArabicReshaper()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()

def process_arabic_text(text):
    """معالجة النص العربي مع التنسيق الصحيح"""
    reshaped = reshaper.reshape(text)
    return get_display(reshaped)

def set_docx_rtl(paragraph):
    """ضبط اتجاه النص لليمين في DOCX"""
    p_pr = paragraph._element.get_or_add_pPr()
    p_bidi = OxmlElement('w:bidi')
    p_pr.append(p_bidi)
    p_jc = OxmlElement('w:jc')
    p_jc.set(qn('w:val'), "right")
    p_pr.append(p_jc)

def translate_docx(file_path):
    """ترجمة ملفات DOCX مع الحفاظ على التنسيق"""
    doc = docx.Document(file_path)
    
    # معالجة الفقرات الرئيسية
    for para in doc.paragraphs:
        full_text = ' '.join(run.text for run in para.runs)
        if full_text.strip():
            try:
                translated = translator.translate(full_text, src='en', dest='ar').text
                processed_text = process_arabic_text(translated)
                
                # مسح المحتوى القديم وإضافة النص الجديد
                para.clear()
                new_run = para.add_run(processed_text)
                
                # ضبط الخط العربي
                new_run.font.name = 'Arial'
                new_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
                
            except Exception as e:
                logger.error(f"DOCX Translation Error: {e}")
        
        set_docx_rtl(para)
    
    # معالجة الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for cell_para in cell.paragraphs:
                    cell_text = ' '.join(run.text for run in cell_para.runs)
                    if cell_text.strip():
                        try:
                            translated = translator.translate(cell_text, src='en', dest='ar').text
                            processed_text = process_arabic_text(translated)
                            
                            cell_para.clear()
                            new_run = cell_para.add_run(processed_text)
                            new_run.font.name = 'Arial'
                            new_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
                            
                        except Exception as e:
                            logger.error(f"Table Translation Error: {e}")
                    
                    set_docx_rtl(cell_para)
    
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """ترجمة ملفات PPTX مع الحفاظ على التنسيق"""
    prs = Presentation(file_path)
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame"):
                for paragraph in shape.text_frame.paragraphs:
                    full_text = ' '.join(run.text for run in paragraph.runs)
                    if full_text.strip():
                        try:
                            translated = translator.translate(full_text, src='en', dest='ar').text
                            processed_text = process_arabic_text(translated)
                            
                            # مسح المحتوى القديم
                            for run in paragraph.runs:
                                run.text = ''
                            
                            # إضافة النص الجديد
                            new_run = paragraph.add_run()
                            new_run.text = processed_text
                            
                            # ضبط الخط والمحاذاة
                            new_run.font.name = 'Arial'
                            paragraph.alignment = PP_ALIGN.RIGHT
                            
                        except Exception as e:
                            logger.error(f"PPTX Translation Error: {e}")
    
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    update.message.reply_text("مرحبا! أرسل ملف DOCX أو PPTX للترجمة إلى العربية.")

def handle_file(update, context):
    file = update.message.document
    filename = file.file_name
    temp_dir = tempfile.gettempdir()
    source_path = os.path.join(temp_dir, filename)
    translated_path = None
    
    try:
        # تنزيل الملف
        file.get_file().download(custom_path=source_path)
        update.message.reply_text("⚙️ جاري المعالجة...")
        
        # الترجمة حسب نوع الملف
        if filename.lower().endswith('.docx'):
            translated_path = translate_docx(source_path)
        elif filename.lower().endswith('.pptx'):
            translated_path = translate_pptx(source_path)
        else:
            update.message.reply_text("❌ الصيغة غير مدعومة! يرجى إرسال DOCX/PPTX فقط.")
            return
        
        # إرسال الملف المترجم
        with open(translated_path, 'rb') as f:
            update.message.reply_document(document=f)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ حدث خطأ أثناء المعالجة!")
        
    finally:
        # تنظيف الملفات المؤقتة
        for path in [source_path, translated_path]:
            if path and os.path.exists(path):
                os.remove(path)

def main():
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
