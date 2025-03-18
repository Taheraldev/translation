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

# إعداد الـ logging لتتبع الأخطاء والعمليات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة المترجم (يفضل استخدام googletrans==4.0.0-rc1)
translator = Translator()

# إعداد إعدادات مكتبة arabic_reshaper كقاموس
arabic_config = {
    'delete_harakat': True,      # حذف الحركات لتقليل التشويه
    'support_ligatures': True     # دعم الربط بين الحروف
}

def set_paragraph_rtl(paragraph):
    """
    تضيف هذه الدالة عنصر XML لتعيين اتجاه الفقرة من اليمين إلى اليسار.
    """
    p = paragraph._p
    pPr = p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr')
        p.insert(0, pPr)
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), "1")
    pPr.append(bidi)

def process_arabic_text(text):
    """
    تعالج النص العربي باستخدام arabic_reshaper مع إعدادات مخصصة ثم تُعيد النص
    مع عرض صحيح باستخدام مكتبة python-bidi.
    """
    reshaped_text = arabic_reshaper.reshape(text, configuration=arabic_config)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def translate_docx(file_path):
    """
    تفتح هذه الدالة ملف DOCX وتترجم النصوص الموجودة فيه، مع عرض سجلات 
    لكل جزء يتم ترجمته.
    """
    doc = docx.Document(file_path)
    
    # ترجمة الفقرات العادية
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                original = run.text
                try:
                    translated = translator.translate(original, src='en', dest='ar')
                    logger.info(f"Original: {original} | Translated: {translated.text}")
                    run.text = process_arabic_text(translated.text)
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص: {original}. الخطأ: {e}")
        set_paragraph_rtl(para)
    
    # ترجمة النصوص داخل الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            original = run.text
                            try:
                                translated = translator.translate(original, src='en', dest='ar')
                                logger.info(f"Original: {original} | Translated: {translated.text}")
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص داخل الجدول: {original}. الخطأ: {e}")
                    set_paragraph_rtl(para)
    
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """
    تفتح هذه الدالة ملف PPTX وتترجم النصوص الموجودة في الشرائح، مع ضبط
    محاذاة النص إلى اليمين وإضافة سجلات لكل ترجمة.
    """
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame") and shape.text_frame is not None:
                for paragraph in shape.text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.RIGHT
                    for run in paragraph.runs:
                        if run.text.strip():
                            original = run.text
                            try:
                                translated = translator.translate(original, src='en', dest='ar')
                                logger.info(f"Original: {original} | Translated: {translated.text}")
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص: {original}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    update.message.reply_text(
        "مرحباً! أرسل لي ملفاً بصيغة DOCX أو PPTX (أو ملفات DOC/PPT بعد تحويلها) لأقوم بترجمته من الإنجليزية إلى العربية."
    )

def handle_file(update, context):
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # تنزيل الملف المرسل إلى مسار مؤقت
    file = context.bot.getFile(document.file_id)
    file.download(custom_path=file_path)
    
    update.message.reply_text("جاري معالجة الملف وترجمته، يرجى الانتظار...")
    
    translated_path = None
    try:
        if filename.endswith('.docx'):
            translated_path = translate_docx(file_path)
        elif filename.endswith('.pptx'):
            translated_path = translate_pptx(file_path)
        elif filename.endswith('.doc'):
            update.message.reply_text(
                "صيغة DOC غير مدعومة مباشرة. الرجاء تحويل الملف إلى DOCX أولاً."
            )
            return
        elif filename.endswith('.ppt'):
            update.message.reply_text(
                "صيغة PPT غير مدعومة مباشرة. الرجاء تحويل الملف إلى PPTX أولاً."
            )
            return
        else:
            update.message.reply_text("صيغة الملف غير مدعومة. الرجاء إرسال ملف بصيغة DOCX أو PPTX.")
            return
        
        # إرسال الملف المترجم للمستخدم
        context.bot.send_document(chat_id=update.message.chat_id, document=open(translated_path, 'rb'))
    except Exception as e:
        logger.error(f"حدث خطأ أثناء ترجمة الملف: {e}")
        update.message.reply_text("حدث خطأ أثناء ترجمة الملف. الرجاء المحاولة مرة أخرى.")
    finally:
        # حذف الملفات المؤقتة
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if translated_path and os.path.exists(translated_path):
                os.remove(translated_path)
        except Exception as cleanup_error:
            logger.warning(f"خطأ أثناء حذف الملفات المؤقتة: {cleanup_error}")

def main():
    # ضع توكن البوت الخاص بك هنا
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
