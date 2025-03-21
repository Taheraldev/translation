import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات FreeConvert API
FREECONVERT_API_KEY = 'YOUR_FREECONVERT_API_KEY'
FREECONVERT_UPLOAD_URL = 'https://api.freeconvert.com/v1/process/import/upload'
FREECONVERT_CONVERT_URL = 'https://api.freeconvert.com/v1/process/convert/pdf-to-docx'
FREECONVERT_EXPORT_URL = 'https://api.freeconvert.com/v1/process/export'

# إعدادات البوت
TELEGRAM_BOT_TOKEN = '5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc'

# إعدادات اللوج
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحباً! أرسل لي ملف PDF وسأقوم بتحويله إلى DOCX.')

def convert_pdf_to_docx(file_path: str) -> str:
    # رفع الملف إلى FreeConvert
    files = {'file': open(file_path, 'rb')}
    headers = {
        'Authorization': f'Bearer {FREECONVERT_API_KEY}'
    }

    # إرسال الطلب لرفع الملف
    upload_response = requests.post(FREECONVERT_UPLOAD_URL, headers=headers, files=files)
    files['file'].close()
    
    if upload_response.status_code != 200:
        return f"فشل رفع الملف: {upload_response.text}"

    task_id = upload_response.json().get('data', {}).get('id')
    
    if not task_id:
        return "لم يتم العثور على ID المهمة، فشل الرفع."

    # تحويل PDF إلى DOCX
    convert_data = {
        'task': task_id
    }
    convert_response = requests.post(FREECONVERT_CONVERT_URL, headers=headers, data=convert_data)
    
    if convert_response.status_code != 200:
        return f"فشل التحويل: {convert_response.text}"

    # استخراج رابط الملف المحول
    export_data = {
        'task': task_id
    }
    export_response = requests.post(FREECONVERT_EXPORT_URL, headers=headers, data=export_data)
    
    if export_response.status_code != 200:
        return f"فشل تصدير الملف: {export_response.text}"
    
    download_url = export_response.json().get('data', {}).get('url')
    if not download_url:
        return "لم يتم العثور على رابط التحميل للملف المحول."

    return download_url

def handle_document(update: Update, context: CallbackContext) -> None:
    # استقبال الملف PDF من المستخدم
    file = update.message.document
    file_id = file.file_id
    new_file = context.bot.get_file(file_id)
    file_path = f"./{file.file_name}"

    # تنزيل الملف
    new_file.download(file_path)
    
    # تحويل PDF إلى DOCX
    download_url = convert_pdf_to_docx(file_path)
    
    if "http" in download_url:
        # إرسال رابط التحميل للمستخدم
        update.message.reply_text(f"تم تحويل الملف بنجاح! يمكنك تنزيله من هنا: {download_url}")
    else:
        # إرسال رسالة في حال حدوث خطأ
        update.message.reply_text(f"حدث خطأ: {download_url}")

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher

    # إضافة المعالج للأوامر
    dispatcher.add_handler(CommandHandler("start", start))
    
    # إضافة معالج للملفات
    dispatcher.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))

    # بدء البوت
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
