import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import docx
from pptx import Presentation
from googletrans import Translator
from pdf import convert_to_pdf, convert_pdf_to  # استيراد دوال تحويل PDF

# إعداد الـ logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

translator = Translator()

def translate_docx(file_path):
    """ترجمة ملف DOCX"""
    doc = docx.Document(file_path)
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = translated.text
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """ترجمة ملف PPTX"""
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame") and shape.text_frame is not None:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = translated.text
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    update.message.reply_text(
        "مرحباً! أرسل لي ملفاً بصيغة DOCX أو PPTX لأقوم بترجمته.\n"
        "يمكنك أيضًا إرسال PDF وسأقوم بتحويله إلى DOCX أو PPTX."
    )

def handle_file(update, context):
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    file = context.bot.getFile(document.file_id)
    file.download(custom_path=file_path)
    
    update.message.reply_text("جاري معالجة الملف، يرجى الانتظار...")
    
    translated_path = None

    try:
        if filename.endswith('.docx'):
            translated_path = translate_docx(file_path)
        elif filename.endswith('.pptx'):
            translated_path = translate_pptx(file_path)
        elif filename.endswith('.pdf'):
            converted_path = convert_pdf_to(file_path, "docx")  # تحويل PDF إلى DOCX
            if converted_path:
                translated_path = translate_docx(converted_path)
            else:
                update.message.reply_text("❌ فشل تحويل PDF إلى DOCX.")
                return
        else:
            update.message.reply_text("صيغة الملف غير مدعومة.")
            return
        
        # إرسال الملف المترجم أو المحول
        context.bot.send_document(chat_id=update.message.chat_id, document=open(translated_path, 'rb'))
    except Exception as e:
        logger.error(f"حدث خطأ أثناء معالجة الملف: {e}")
        update.message.reply_text("❌ حدث خطأ أثناء معالجة الملف.")
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if translated_path and os.path.exists(translated_path):
                os.remove(translated_path)
        except Exception as cleanup_error:
            logger.warning(f"خطأ أثناء حذف الملفات المؤقتة: {cleanup_error}")

def pdf_command(update, context):
    """أمر لتحويل ملف إلى PDF"""
    update.message.reply_text("أرسل لي ملف DOCX أو PPTX وسأحوله إلى PDF.")

def handle_pdf_conversion(update, context):
    """التعامل مع تحويل DOCX أو PPTX إلى PDF"""
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    file = context.bot.getFile(document.file_id)
    file.download(custom_path=file_path)
    
    if filename.endswith('.docx') or filename.endswith('.pptx'):
        converted_path = convert_to_pdf(file_path)
        if converted_path:
            context.bot.send_document(chat_id=update.message.chat_id, document=open(converted_path, 'rb'))
        else:
            update.message.reply_text("❌ فشل تحويل الملف إلى PDF.")
    else:
        update.message.reply_text("❌ الرجاء إرسال ملف بصيغة DOCX أو PPTX فقط.")

def main():
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("pdf", pdf_command))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    dp.add_handler(MessageHandler(Filters.document, handle_pdf_conversion))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
