import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import docx
from pptx import Presentation
from googletrans import Translator

# إعداد الـ logging (اختياري)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة المترجم (يمكن استخدام API رسمي إذا لزم الأمر)
translator = Translator()

def translate_docx(file_path):
    """
    تفتح ملف DOCX وتترجم محتواه على مستوى كل run للحفاظ على التنسيق.
    """
    doc = docx.Document(file_path)
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = translated.text
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة نص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """
    تفتح ملف PPTX وتترجم محتوى الشرائح.
    """
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
                                logger.error(f"خطأ أثناء ترجمة نص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    update.message.reply_text("مرحباً! أرسل لي ملفاً بصيغة DOCX أو PPTX (أو ملفات DOC/PPT بعد تحويلها) لأقوم بترجمته من الإنجليزية إلى العربية.")

def handle_file(update, context):
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # تنزيل الملف
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
            update.message.reply_text("صيغة DOC غير مدعومة مباشرة. يرجى تحويل الملف إلى DOCX أولاً (يمكن استخدام LibreOffice للتحويل).")
            return
        elif filename.endswith('.ppt'):
            update.message.reply_text("صيغة PPT غير مدعومة مباشرة. يرجى تحويل الملف إلى PPTX أولاً (يمكن استخدام LibreOffice للتحويل).")
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
        # تنظيف الملفات المؤقتة
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if translated_path and os.path.exists(translated_path):
                os.remove(translated_path)
        except Exception as cleanup_error:
            logger.warning(f"خطأ أثناء حذف الملفات المؤقتة: {cleanup_error}")

def main():
    # ضع توكن البوت الخاص بك هنا
    TOKEN = "6016945663:AAHjacRdRfZ2vUgS2SLmoFgHfMdUye4l6bA"
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # أوامر البوت
    dp.add_handler(CommandHandler("start", start))
    
    # التعامل مع الملفات المرسلة
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
