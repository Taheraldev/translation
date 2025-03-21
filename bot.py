import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from convertapi import ConvertApi  

# إعدادات ConvertAPI
ConvertApi.secret = 'secret_lFUCQ7x8MrYAJHsk'  # الطريقة القديمة
# إعدادات ConvertAPI
# باقي الإعدادات بدون تغيير
TOKEN = "5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc"

SUPPORTED_CONVERSIONS = {
    'application/pdf': {
        'target_format': 'docx',
        'response_text': 'تم تحويل PDF إلى DOCX بنجاح!'
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'target_format': 'pdf',
        'response_text': 'تم تحويل DOCX إلى PDF بنجاح!'
    },
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': {
        'target_format': 'pdf',
        'response_text': 'تم تحويل PPTX إلى PDF بنجاح!'
    }
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    help_text = (
        "مرحبًا! أنا بوت التحويل الذكي 🤖\n"
        "يمكنني تحويل:\n"
        "▫️ PDF → DOCX\n"
        "▫️ DOCX → PDF\n"
        "▫️ PPTX → PDF\n"
        "أرسل الملف وسأقوم بالتحويل تلقائيًا!"
    )
    update.message.reply_text(help_text)

def handle_document(update, context):
    file = update.message.document
    mime_type = file.mime_type

    if mime_type not in SUPPORTED_CONVERSIONS:
        update.message.reply_text("⚠️ الصيغة غير مدعومة! الرجاء إرسال ملف PDF أو DOCX أو PPTX.")
        return

    try:
        # تنزيل الملف
        file_id = file.file_id
        new_file = context.bot.get_file(file_id)
        file_ext = mime_type.split('/')[-1]  # إصلاح هنا
        input_path = f"temp_{file_id}.{file_ext}"
        new_file.download(input_path)

        # إعداد التحويل
        conversion = SUPPORTED_CONVERSIONS[mime_type]
        target_format = conversion['target_format']
        output_path = f"converted_{file_id}.{target_format}"

        # التحويل باستخدام الإصدار 1.8.0
        result = ConvertApi().convert(  # التعديل هنا
            target_format,
            {'File': input_path}
        )
        result.save_files(output_path)

        # إرسال الملف المحول
        with open(output_path, 'rb') as output_file:
            update.message.reply_document(
                document=output_file,
                caption=conversion['response_text']
            )

        # تنظيف الملفات
        os.remove(input_path)
        os.remove(output_path)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ فشل التحويل! الرجاء التأكد من صحة الملف.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
