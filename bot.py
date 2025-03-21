import os
import convertapi
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات البوت
TELEGRAM_BOT_TOKEN = '5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc'
CONVERT_API_SECRET = 'secret_lFUCQ7x8MrYAJHsk'
convertapi.api_secret = CONVERT_API_SECRET

# تفعيل نظام تسجيل الأحداث (للتصحيح)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("أهلاً! أرسل لي ملف PDF وسأقوم بتحويله إلى DOCX أو PPTX.")

def handle_document(update: Update, context: CallbackContext):
    document = update.message.document

    # التحقق من أن الملف PDF
    if document.mime_type != 'application/pdf':
        update.message.reply_text("يرجى إرسال ملف PDF فقط.")
        return

    file = context.bot.getFile(document.file_id)
    pdf_filename = document.file_name

    # تحميل الملف من تليجرام
    file.download(pdf_filename)

    # نوع التحويل المطلوب (يمكن تعديله لاحقاً)
    target_format = 'docx'  # غيّره إلى 'pptx' لتحويل إلى عرض تقديمي

    try:
        # استخدام ConvertAPI لتحويل الملف
        result = convertapi.convert(target_format, {'File': pdf_filename})
        output_filename = f'converted.{target_format}'
        result.file.save(output_filename)

        # إرسال الملف المحول
        with open(output_filename, 'rb') as converted_file:
            update.message.reply_document(document=converted_file, filename=output_filename, caption=f"تم تحويل الملف إلى {target_format.upper()} بنجاح.")

    except Exception as e:
        update.message.reply_text(f"حدث خطأ أثناء التحويل: {e}")

    finally:
        # حذف الملفات المؤقتة
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # أوامر البوت
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    # بدء تشغيل البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
