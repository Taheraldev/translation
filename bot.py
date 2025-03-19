import os
import requests
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد السجل logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد بيانات Smartcat API من المثال
SMARTCAT_SERVER = "https://smartcat.com"
WORKSPACE_ID = "63b1e7ba-ecdc-4978-a1a9-d27dd36d5b48"
PROJECT_ID = "21355320-aee6-4b65-966f-a810e802b81a"
API_TOKEN = "2_FwEmd5QMpKxDbHnNnwydzEL3o"

# إعداد المصادقة باستخدام ApiToken
headers_auth = {
    'Authorization': f'Bearer {API_TOKEN}'
}

# نقطة النهاية للترجمة (يمكنك التحقق من التوثيق للحصول على الـ endpoint الصحيح)
SMARTCAT_ENDPOINT = f"{SMARTCAT_SERVER}/api/integration/v1/translate"

# إعداد لغات المصدر والهدف
SOURCE_LANG = 'en'
TARGET_LANG = 'ar'

def start(update: Update, context: CallbackContext) -> None:
    """معالجة أمر /start"""
    update.message.reply_text('مرحباً! أرسل لي ملف PDF لأقوم بترجمته إلى العربية وتحويله إلى DOCX.')

def translate_file(file_path: str, output_path: str) -> bool:
    """
    ترسل هذه الدالة الملف بصيغة PDF إلى Smartcat API للترجمة من الإنجليزية إلى العربية
    وتحويل الملف إلى صيغة DOCX.
    تحفظ الدالة الملف المترجم في output_path وتعيد True في حال النجاح.
    """
    with open(file_path, 'rb') as f:
        files = {
            'file': ('input.pdf', f, 'application/pdf')
        }
        # البيانات المطلوبة لعملية الترجمة
        data = {
            'source_lang': SOURCE_LANG,
            'target_lang': TARGET_LANG,
            'output_format': 'docx',
            'workspace_id': WORKSPACE_ID,
            'project_id': PROJECT_ID
        }
        try:
            response = requests.post(SMARTCAT_ENDPOINT, files=files, data=data, headers=headers_auth)
            if response.status_code == 200:
                # حفظ الملف المترجم
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                return True
            else:
                logger.error(f"خطأ من Smartcat API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"استثناء أثناء الاتصال بـ Smartcat API: {e}")
            return False

def handle_document(update: Update, context: CallbackContext) -> None:
    """معالجة الملفات المرسلة من المستخدم"""
    document = update.message.document
    # التأكد من أن الملف بصيغة PDF
    if document.mime_type != 'application/pdf':
        update.message.reply_text('يرجى إرسال ملف بصيغة PDF فقط.')
        return
    
    file_id = document.file_id
    new_file = context.bot.get_file(file_id)
    input_file_path = 'input.pdf'
    output_file_path = 'translated.docx'
    
    # تحميل الملف من تليجرام
    new_file.download(custom_path=input_file_path)
    update.message.reply_text('جارٍ الترجمة، يرجى الانتظار...')
    
    # إرسال الملف للترجمة
    success = translate_file(input_file_path, output_file_path)
    
    if success:
        with open(output_file_path, 'rb') as docx_file:
            update.message.reply_document(document=docx_file, filename='translated.docx')
        update.message.reply_text('تمت الترجمة بنجاح!')
        # حذف الملفات المؤقتة
        os.remove(input_file_path)
        os.remove(output_file_path)
    else:
        update.message.reply_text('حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى لاحقاً.')

def main() -> None:
    """الدالة الرئيسية لتشغيل البوت"""
    # استبدل 'YOUR_TELEGRAM_BOT_TOKEN' برمز البوت الخاص بك
    updater = Updater("5284087690:AAGwKfPojQ3c-SjCHSIdeog-yN3-4Gpim1Y", use_context=True)
    dispatcher = updater.dispatcher
    
    # إضافة معالجات الأوامر والرسائل
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
    
    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
