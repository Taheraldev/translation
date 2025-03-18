import os
import logging
import convertapi
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# إعدادات ConvertAPI (متوافق مع الإصدار 1.5.0)
convertapi.api_secret = 'secret_q4ijKpkWw17sLQx8'  # المفتاح السري

# إعدادات البوت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# خريطة التحويل المدعومة
SUPPORTED_CONVERSIONS = {
    'application/pdf': {
        'target_format': 'docx',
        'response_text': 'تم تحويل PDF إلى DOCX بنجاح!',
        'requires_topdf': False  # لا يحتاج إلى أمر /topdf
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'target_format': 'pdf',
        'response_text': 'تم تحويل DOCX إلى PDF بنجاح!',
        'requires_topdf': True  # يحتاج إلى أمر /topdf
    },
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': {
        'target_format': 'pdf',
        'response_text': 'تم تحويل PPTX إلى PDF بنجاح!',
        'requires_topdf': True  # يحتاج إلى أمر /topdf
    }
}

# تخزين المستخدمين الذين أرسلوا /topdf
users_with_topdf = set()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    help_text = (
        "مرحبًا! أنا بوت التحويل الذكي 🤖\n"
        "يمكنني تحويل:\n"
        "▫️ PDF → DOCX (تلقائيًا)\n"
        "▫️ DOCX → PDF (يجب إرسال /topdf قبل الملف)\n"
        "▫️ PPTX → PDF (يجب إرسال /topdf قبل الملف)\n"
        "أرسل الملف وسأقوم بالتحويل تلقائيًا!"
    )
    update.message.reply_text(help_text)

def topdf(update, context):
    """تفعيل تحويل DOCX و PPTX إلى PDF عند إرسال الملفات"""
    users_with_topdf.add(update.message.chat_id)
    update.message.reply_text("✅ تم تفعيل تحويل DOCX و PPTX إلى PDF. أرسل الملف الآن.")

def handle_document(update, context):
    file = update.message.document
    mime_type = file.mime_type

    if mime_type not in SUPPORTED_CONVERSIONS:
        update.message.reply_text("⚠️ الصيغة غير مدعومة! الرجاء إرسال ملف PDF أو DOCX أو PPTX.")
        return

    conversion = SUPPORTED_CONVERSIONS[mime_type]
    
    # التحقق من الحاجة إلى /topdf
    if conversion['requires_topdf'] and update.message.chat_id not in users_with_topdf:
        update.message.reply_text("⚠️ يجب إرسال /topdf أولًا قبل إرسال الملف.")
        return

    try:
        # تنزيل الملف
        file_id = file.file_id
        new_file = context.bot.get_file(file_id)
        file_ext = mime_type.split('.')[-1]
        input_path = f"temp_{file_id}.{file_ext}"
        new_file.download(input_path)

        # تنفيذ التحويل باستخدام ConvertAPI
        target_format = conversion['target_format']
        output_path = f"converted_{file_id}.{target_format}"

        result = convertapi.convert(target_format, {'File': input_path})
        result.save_files(output_path)

        # إرسال الملف المحول
        with open(output_path, 'rb') as output_file:
            update.message.reply_document(
                document=output_file,
                caption=conversion['response_text']
            )

        # تنظيف الملفات المؤقتة
        os.remove(input_path)
        os.remove(output_path)

        # إزالة المستخدم من قائمة /topdf بعد استخدامه
        if update.message.chat_id in users_with_topdf:
            users_with_topdf.remove(update.message.chat_id)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ فشل التحويل! الرجاء التأكد من صحة الملف.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("topdf", topdf))  # إضافة أمر /topdf
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
