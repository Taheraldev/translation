import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import docx
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد الـ logging لتتبع الأخطاء والعمليات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة المترجم (يمكنكم استبداله بخدمة ترجمة مدفوعة للحصول على دقة أعلى)
translator = Translator()

def process_arabic_text(text):
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        logger.error(f"Error processing Arabic text: {e}")
        return text

def translate_docx(file_path):
    doc = docx.Document(file_path)
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = process_arabic_text(translated.text)
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
        para.paragraph_format.right_to_left = True

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
                                logger.error(f"خطأ أثناء ترجمة النص داخل الجدول: {run.text}. الخطأ: {e}")
                    para.paragraph_format.right_to_left = True

    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
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
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    update.message.reply_text("مرحباً! أرسل لي ملفاً بصيغة DOCX أو PPTX لأقوم بترجمته.")

def handle_file(update, context):
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    file = context.bot.getFile(document.file_id)
    file.download(custom_path=file_path)
    update.message.reply_text("جاري معالجة الملف وترجمته، يرجى الانتظار...")
    translated_path = None
    try:
        if filename.endswith('.docx'):
            translated_path = translate_docx(file_path)
        elif filename.endswith('.pptx'):
            translated_path = translate_pptx(file_path)
        else:
            update.message.reply_text("صيغة الملف غير مدعومة. الرجاء إرسال ملف بصيغة DOCX أو PPTX.")
            return
        context.bot.send_document(chat_id=update.message.chat_id, document=open(translated_path, 'rb'))
    except Exception as e:
        logger.error(f"حدث خطأ أثناء ترجمة الملف: {e}")
        update.message.reply_text("حدث خطأ أثناء ترجمة الملف. الرجاء المحاولة مرة أخرى.")
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if translated_path and os.path.exists(translated_path):
                os.remove(translated_path)
        except Exception as cleanup_error:
            logger.warning(f"خطأ أثناء حذف الملفات المؤقتة: {cleanup_error}")

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
