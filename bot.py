import logging
import os
from tempfile import NamedTemporaryFile

import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات التهيئة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مفتاح API من convertapi
CONVERT_API_SECRET = 'secret_lFUCQ7x8MrYAJHsk'
CONVERT_API_URL = 'https://v2.convertapi.com/convert/pdf/to/docx'

def start(update: Update, context: CallbackContext):
    """يرسل رسالة ترحيب عند استخدام الأمر /start"""
    update.message.reply_text(
        'مرحبا! أرسل لي ملف PDF وسأحوله إلى مستند Word (DOCX) لك.'
    )

def handle_pdf(update: Update, context: CallbackContext):
    """يتعامل مع ملفات PDF المرسلة"""
    user = update.message.from_user
    document = update.message.document

    # التحقق من نوع الملف
    if document.mime_type != 'application/pdf':
        update.message.reply_text('يرجى إرسال ملف PDF فقط.')
        return

    try:
        # تنزيل ملف PDF
        pdf_file = context.bot.get_file(document.file_id)
        pdf_path = f'{document.file_id}.pdf'
        pdf_file.download(pdf_path)

        # إرسال الملف إلى ConvertAPI
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                CONVERT_API_URL,
                params={'secret': CONVERT_API_SECRET},
                files={'File': (pdf_path, f)}
            )

        # التحقق من نجاح التحويل
        if response.status_code != 200:
            raise Exception(f'خطأ في التحويل: {response.status_code}')

        # إنشاء ملف مؤقت لحفظ النتيجة
        with NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        # إرسال الملف المحول للمستخدم
        with open(temp_path, 'rb') as docx_file:
            update.message.reply_document(
                document=docx_file,
                filename=f'{document.file_name}.docx'
            )

    except Exception as e:
        logger.error(e)
        update.message.reply_text('حدث خطأ أثناء معالجة الملف. يرجى المحاولة لاحقًا.')
    
    finally:
        # تنظيف الملفات المؤقتة
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    """تشغيل البوت"""
    # استبدل 'YOUR_BOT_TOKEN' بتوكن البوت الخاص بك
    updater = Updater(token='5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc', use_context=True)
    dp = updater.dispatcher

    # إضافة handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.document, handle_pdf))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
