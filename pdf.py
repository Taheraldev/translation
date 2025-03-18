import os
import logging
from convertapi import ConvertApi  # استخدام الإصدار الصحيح
from telegram import Update
from telegram.ext import CallbackContext

# إعدادات ConvertAPI
ConvertApi.api_secret = 'secret_q4ijKpkWw17sLQx8'  # المفتاح السري

# خريطة التحويل المدعومة
SUPPORTED_CONVERSIONS = {
    'application/pdf': {
        'target_format': 'docx',
        'response_text': '✅ تم تحويل PDF إلى DOCX بنجاح!'
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'target_format': 'pdf',
        'response_text': '✅ تم تحويل DOCX إلى PDF بنجاح!'
    },
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': {
        'target_format': 'pdf',
        'response_text': '✅ تم تحويل PPTX إلى PDF بنجاح!'
    }
}

# قاموس لتخزين حالة كل مستخدم
user_conversion_modes = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def enable_pdf_conversion(update: Update, context: CallbackContext):
    """تفعيل وضع تحويل DOCX/PPTX إلى PDF عند إرسال الأمر /topdf."""
    user_id = update.message.chat_id
    user_conversion_modes[user_id] = True
    update.message.reply_text("🔄 الآن يمكنك إرسال ملفات DOCX أو PPTX لتحويلها إلى PDF.")

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    mime_type = file.mime_type
    user_id = update.message.chat_id

    # تحقق مما إذا كان التحويل متاحًا للصيغة المطلوبة
    if mime_type not in SUPPORTED_CONVERSIONS:
        update.message.reply_text("⚠️ الصيغة غير مدعومة! الرجاء إرسال ملف PDF فقط أو استخدم /topdf لتحويل DOCX/PPTX إلى PDF.")
        return

    # إذا كان الملف DOCX أو PPTX، نحتاج إلى التأكد من أن المستخدم فعل وضع /topdf
    if mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
        if not user_conversion_modes.get(user_id, False):
            update.message.reply_text("🚫 لتحويل DOCX أو PPTX إلى PDF، يرجى إرسال الأمر /topdf أولًا.")
            return
        else:
            # بعد التحويل، نعطل وضع /topdf حتى لا يتم التحويل تلقائيًا مرة أخرى
            user_conversion_modes[user_id] = False

    try:
        # تنزيل الملف
        file_id = file.file_id
        new_file = context.bot.get_file(file_id)
        file_ext = mime_type.split('.')[-1]
        input_path = f"temp_{file_id}.{file_ext}"
        new_file.download(input_path)

        # إعداد التحويل
        conversion = SUPPORTED_CONVERSIONS[mime_type]
        target_format = conversion['target_format']
        output_path = f"converted_{file_id}.{target_format}"

        # تنفيذ التحويل باستخدام ConvertApi
        result = ConvertApi.convert(target_format, {'File': input_path})
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

    except Exception as e:
        logger.error(f"❌ خطأ أثناء التحويل: {str(e)}")
        update.message.reply_text("❌ فشل التحويل! الرجاء التأكد من صحة الملف.")
