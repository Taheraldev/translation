import os
import logging
import convertapi
from telegram import Update
from telegram.ext import CallbackContext

# إعدادات ConvertAPI (متوافق مع الإصدار 1.5.0)
convertapi.api_secret = 'secret_q4ijKpkWw17sLQx8'  # المفتاح السري

# خريطة التحويل المدعومة
SUPPORTED_CONVERSIONS = {
    'application/pdf': {
        'target_format': 'docx',
        'response_text': '✅ تم تحويل PDF إلى DOCX بنجاح!',
        'requires_topdf': False
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'target_format': 'pdf',
        'response_text': '✅ تم تحويل DOCX إلى PDF بنجاح!',
        'requires_topdf': True
    },
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': {
        'target_format': 'pdf',
        'response_text': '✅ تم تحويل PPTX إلى PDF بنجاح!',
        'requires_topdf': True
    }
}

# تخزين معرفات الدردشات التي فعلت أمر /topdf
users_with_topdf = set()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def topdf(update: Update, context: CallbackContext):
    """تفعيل تحويل DOCX و PPTX إلى PDF عند إرسال الملفات"""
    users_with_topdf.add(update.message.chat_id)
    update.message.reply_text("✅ تم تفعيل تحويل DOCX و PPTX إلى PDF. أرسل الملف الآن.")

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    mime_type = file.mime_type
    user_id = update.message.chat_id

    if mime_type not in SUPPORTED_CONVERSIONS:
        update.message.reply_text("⚠️ الصيغة غير مدعومة! الرجاء إرسال ملف PDF أو DOCX أو PPTX.")
        return

    conversion = SUPPORTED_CONVERSIONS[mime_type]
    
    # التحقق مما إذا كان الملف DOCX/PPTX يحتاج إلى تفعيل /topdf
    if conversion.get('requires_topdf', False) and user_id not in users_with_topdf:
        update.message.reply_text("⚠️ يجب إرسال /topdf أولًا قبل إرسال الملف.")
        return

    try:
        # تنزيل الملف: استخدم اسم الملف للحصول على الامتداد الصحيح
        file_id = file.file_id
        file_name = file.file_name
        file_ext = file_name.split('.')[-1]
        input_path = f"temp_{file_id}.{file_ext}"
        new_file = context.bot.get_file(file_id)
        new_file.download(input_path)

        # إعداد التحويل
        target_format = conversion['target_format']
        output_path = f"converted_{file_id}.{target_format}"

        # تنفيذ التحويل باستخدام ConvertAPI
        result = convertapi.convert(target_format, {'File': input_path})
        result.save_files(output_path)

        # إرسال الملف المحول للمستخدم
        with open(output_path, 'rb') as output_file:
            update.message.reply_document(
                document=output_file,
                caption=conversion['response_text']
            )

        # تنظيف الملفات المؤقتة
        os.remove(input_path)
        os.remove(output_path)

        # إزالة المستخدم من القائمة بعد استخدامه لأمر /topdf
        if user_id in users_with_topdf:
            users_with_topdf.remove(user_id)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ فشل التحويل! الرجاء التأكد من صحة الملف.")
