import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import docx
from docx.shared import Pt
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import arabic_reshaper
from bidi.algorithm import get_display
import convertapi  # إصدار convertapi==1.5.0

# إعداد الـ logging لتتبع الأخطاء والعمليات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد ConvertAPI بالمفتاح السري
convertapi.api_secret = 'secret_q4ijKpkWw17sLQx8'

# تهيئة المترجم (يمكن استبداله بخدمة ترجمة مدفوعة للحصول على دقة أعلى)
translator = Translator()

def set_paragraph_rtl(paragraph):
    """
    تضيف هذه الدالة عنصر XML يُحدد أن الفقرة يجب أن تُعرض من اليمين لليسار.
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
    تعالج النص العربي باستخدام arabic_reshaper و python-bidi لتظهر الحروف بشكل صحيح.
    كما تزيل الفراغات الزائدة في حال كانت الكلمة عبارة عن حروف مفردة مفصولة بمسافات.
    """
    cleaned_text = text.strip()
    parts = cleaned_text.split()
    # إذا كان كل جزء حرف مفرد (أي الكلمة مفصولة حروفاً) نجمعها بدون مسافات
    if parts and all(len(part) == 1 for part in parts) and len(parts) > 1:
        cleaned_text = "".join(parts)
    reshaped_text = arabic_reshaper.reshape(cleaned_text, reshape_ligature=True)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def translate_docx(file_path):
    """
    تقوم هذه الدالة بفتح ملف DOCX وترجمة النصوص الموجودة فيه:
    - الفقرات العادية خارج الجداول.
    - النصوص داخل خلايا الجداول.
    كما تُعيّن خط "Traditional Arabic" لكل نص وتضبط اتجاه الفقرة.
    """
    doc = docx.Document(file_path)
    
    # ترجمة الفقرات العادية
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = process_arabic_text(translated.text)
                    run.font.name = "Traditional Arabic"
                    # يمكن تعيين حجم الخط إذا لزم الأمر
                    run.font.size = Pt(12)
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
        set_paragraph_rtl(para)
    
    # ترجمة النصوص داخل الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                                run.font.name = "Traditional Arabic"
                                run.font.size = Pt(12)
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص داخل الجدول: {run.text}. الخطأ: {e}")
                    set_paragraph_rtl(para)
    
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """
    تقوم هذه الدالة بفتح ملف PPTX وترجمة النصوص الموجودة داخل الشرائح.
    كما تُعيّن محاذاة النص إلى اليمين وتحدد خط "Traditional Arabic" لكل نص.
    """
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame") and shape.text_frame is not None:
                for paragraph in shape.text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.RIGHT
                    for run in paragraph.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                                # تعيين الخط في PPTX (قد يختلف تأثيره حسب القالب)
                                run.font.name = "Traditional Arabic"
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def convert_api(input_path, target_format, output_path):
    """
    تستخدم هذه الدالة ConvertAPI لتحويل الملف إلى الصيغة المطلوبة.
    """
    try:
        result = convertapi.convert(target_format, {'File': input_path})
        result.save_files(output_path)
        logger.info(f"تم تحويل الملف إلى {target_format} بنجاح: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"خطأ أثناء تحويل الملف باستخدام ConvertAPI: {e}")
        return None

def start(update, context):
    help_text = (
        "مرحبًا! أنا بوت الترجمة والتحويل.\n"
        "يمكنك إرسال ملف من الصيغ التالية:\n"
        "▫️ DOCX / PPTX (وإن كان ملف DOC أو PPT بعد التحويل)\n"
        "▫️ PDF\n"
        "وسيتم ترجمة الملف من الإنجليزية إلى العربية، بالإضافة إلى تحويله إلى PDF."
    )
    update.message.reply_text(help_text)

def handle_file(update, context):
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # تنزيل الملف المرسل إلى مسار مؤقت
    file = context.bot.get_file(document.file_id)
    file.download(custom_path=file_path)
    
    update.message.reply_text("جاري معالجة الملف، يرجى الانتظار...")
    
    translated_file = None
    converted_pdf = None
    
    try:
        if filename.endswith('.doc') or filename.endswith('.ppt'):
            update.message.reply_text(
                "صيغة DOC أو PPT غير مدعومة مباشرة. الرجاء تحويل الملف إلى DOCX أو PPTX أولاً."
            )
            return
        
        elif filename.endswith('.pdf'):
            # تحويل ملف PDF إلى DOCX باستخدام ConvertAPI
            converted_docx_path = file_path.replace('.pdf', '_converted.docx')
            conversion_result = convert_api(file_path, 'docx', converted_docx_path)
            if not conversion_result:
                update.message.reply_text("حدث خطأ أثناء تحويل ملف PDF إلى DOCX.")
                return
            # ترجمة الملف المحول (DOCX)
            translated_file = translate_docx(conversion_result)
            # تحويل الملف المترجم إلى PDF باستخدام ConvertAPI
            converted_pdf = translated_file.replace('_translated.docx', '_translated.pdf')
            pdf_conversion_result = convert_api(translated_file, 'pdf', converted_pdf)
            if not pdf_conversion_result:
                update.message.reply_text("حدث خطأ أثناء تحويل الملف المترجم إلى PDF.")
                return
            # إرسال الملف المترجم بصيغة DOCX
            with open(translated_file, 'rb') as doc_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=doc_file,
                    caption="هذا هو الملف المترجم بصيغة DOCX"
                )
            # إرسال الملف المترجم بصيغة PDF
            with open(converted_pdf, 'rb') as pdf_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=pdf_file,
                    caption="هذا هو الملف المترجم بصيغة PDF"
                )
        
        elif filename.endswith('.docx'):
            # ترجمة ملف DOCX
            translated_file = translate_docx(file_path)
            # تحويل الملف المترجم إلى PDF باستخدام ConvertAPI
            converted_pdf = translated_file.replace('_translated.docx', '_translated.pdf')
            pdf_conversion_result = convert_api(translated_file, 'pdf', converted_pdf)
            if not pdf_conversion_result:
                update.message.reply_text("حدث خطأ أثناء تحويل الملف المترجم إلى PDF.")
                return
            # إرسال الملف المترجم بصيغة DOCX
            with open(translated_file, 'rb') as doc_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=doc_file,
                    caption="هذا هو الملف المترجم بصيغة DOCX"
                )
            # إرسال الملف المترجم بصيغة PDF
            with open(converted_pdf, 'rb') as pdf_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=pdf_file,
                    caption="هذا هو الملف المترجم بصيغة PDF"
                )
        
        elif filename.endswith('.pptx'):
            # ترجمة ملف PPTX
            translated_file = translate_pptx(file_path)
            # تحويل الملف المترجم إلى PDF باستخدام ConvertAPI
            converted_pdf = translated_file.replace('_translated.pptx', '_translated.pdf')
            pdf_conversion_result = convert_api(translated_file, 'pdf', converted_pdf)
            if not pdf_conversion_result:
                update.message.reply_text("حدث خطأ أثناء تحويل الملف المترجم إلى PDF.")
                return
            # إرسال الملف المترجم بصيغة PPTX
            with open(translated_file, 'rb') as ppt_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=ppt_file,
                    caption="هذا هو الملف المترجم بصيغة PPTX"
                )
            # إرسال الملف المترجم بصيغة PDF
            with open(converted_pdf, 'rb') as pdf_file:
                context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=pdf_file,
                    caption="هذا هو الملف المترجم بصيغة PDF"
                )
        else:
            update.message.reply_text(
                "صيغة الملف غير مدعومة. الرجاء إرسال ملف بصيغة DOCX, PPTX أو PDF."
            )
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء معالجة الملف: {e}")
        update.message.reply_text("حدث خطأ أثناء معالجة الملف. الرجاء المحاولة مرة أخرى.")
    
    finally:
        # تنظيف الملفات المؤقتة
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if 'converted_docx_path' in locals() and os.path.exists(converted_docx_path):
                os.remove(converted_docx_path)
            if translated_file and os.path.exists(translated_file):
                os.remove(translated_file)
            if converted_pdf and os.path.exists(converted_pdf):
                os.remove(converted_pdf)
        except Exception as cleanup_error:
            logger.warning(f"خطأ أثناء حذف الملفات المؤقتة: {cleanup_error}")

def main():
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"  # استبدل هذا بتوكن البوت الخاص بك
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
