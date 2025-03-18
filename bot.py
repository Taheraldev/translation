import os
import tempfile
import logging
import convertapi
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import docx
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF  # إضافة مكتبة FPDF لإنشاء PDF يدويًا

# إعدادات ConvertAPI
convertapi.api_secret = 'secret_q4ijKpkWw17sLQx8'  # استبدال بالمفتاح الخاص بك

# إعدادات الترجمة
translator = Translator()

# إعدادات البوت
TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"

# إعداد الـ logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def set_paragraph_rtl(paragraph):
    """تعديل اتجاه الفقرة لليمين-لليسار"""
    p = paragraph._p
    pPr = p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr')
        p.insert(0, pPr)
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), "1")
    pPr.append(bidi)

def process_arabic_text(text):
    """معالجة النص العربي للتنسيق الصحيح"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def create_pdf_from_text(text, output_path):
    """إنشاء ملف PDF يدويًا مع معالجة النصوص العربية"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)  # تأكد من وجود خط يدعم العربية
    pdf.set_font('DejaVu', '', 12)
    pdf.multi_cell(0, 10, txt=text, align='R')  # محاذاة النص لليمين
    pdf.output(output_path)

def translate_docx(file_path):
    """ترجمة ملفات DOCX مع الحفاظ على التنسيق"""
    doc = docx.Document(file_path)
    
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = process_arabic_text(translated.text)
                except Exception as e:
                    logger.error(f"Translation error: {e}")
        set_paragraph_rtl(para)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"Translation error: {e}")
                    set_paragraph_rtl(para)
    
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
                    paragraph.alignment = PP_ALIGN.RIGHT
                    for run in paragraph.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"Translation error: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def handle_document(update: Update, context: CallbackContext):
    """معالجة الملفات الواردة"""
    document = update.message.document
    mime_type = document.mime_type
    file_id = document.file_id
    filename = document.file_name.lower()
    temp_files = []

    try:
        # تنزيل الملف
        file = context.bot.get_file(file_id)
        temp_dir = tempfile.gettempdir()
        input_path = os.path.join(temp_dir, filename)
        file.download(custom_path=input_path)
        temp_files.append(input_path)

        # تحديد نوع المعالجة
        if mime_type in [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]:
            # ترجمة الملف
            if 'word' in mime_type:
                translated_path = translate_docx(input_path)
                target_format = 'docx'
            else:
                translated_path = translate_pptx(input_path)
                target_format = 'pptx'
            temp_files.append(translated_path)

            # إنشاء PDF يدويًا
            output_pdf = translated_path.replace(f'_{target_format}', '_converted.pdf')
            if target_format == 'docx':
                doc = docx.Document(translated_path)
                full_text = "\n".join([para.text for para in doc.paragraphs])
            else:
                prs = Presentation(translated_path)
                full_text = "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
            
            create_pdf_from_text(full_text, output_pdf)
            temp_files.append(output_pdf)

            # إرسال النتائج
            update.message.reply_document(document=open(translated_path, 'rb'), caption="📄 الملف المترجم")
            update.message.reply_document(document=open(output_pdf, 'rb'), caption="🖨️ النسخة PDF")

        elif mime_type == 'application/pdf':
            # تحويل PDF إلى DOCX
            converted_docx = input_path.replace('.pdf', '_converted.docx')
            convertapi.convert(
                'docx',
                {'File': input_path},
                from_format='pdf'
            ).save_files(converted_docx)
            temp_files.append(converted_docx)

            # ترجمة DOCX
            translated_docx = translate_docx(converted_docx)
            temp_files.append(translated_docx)

            # إنشاء PDF يدويًا
            translated_pdf = translated_docx.replace('.docx', '_converted.pdf')
            doc = docx.Document(translated_docx)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            create_pdf_from_text(full_text, translated_pdf)
            temp_files.append(translated_pdf)

            # إرسال النتائج
            update.message.reply_document(document=open(translated_docx, 'rb'), caption="📄 DOCX المترجم")
            update.message.reply_document(document=open(translated_pdf, 'rb'), caption="🖨️ PDF المترجم")

        elif mime_type in ['application/msword', 'application/vnd.ms-powerpoint']:
            update.message.reply_text("⚠️ الرجاء تحويل الملف إلى DOCX/PPTX أولاً (استخدم LibreOffice).")

        else:
            update.message.reply_text("❌ الصيغة غير مدعومة!")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ فشلت العملية! تأكد من صحة الملف.")
    finally:
        # تنظيف الملفات المؤقتة
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Error deleting {path}: {e}")

def main():
    """تشغيل البوت"""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
