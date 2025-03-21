import os
import requests
import logging
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()
API_KEY = os.getenv('FREE_CONVERT_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رؤوس HTTP للـ API
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

def start(update: Update, context: CallbackContext):
    """معالجة أمر /start"""
    user = update.effective_user
    update.message.reply_text(f"مرحبًا {user.first_name}! أرسل لي ملف PDF وسأحوله إلى DOCX.")

def handle_pdf(update: Update, context: CallbackContext):
    """معالجة ملفات PDF المرسلة"""
    try:
        # تنزيل الملف
        logger.info("جاري تنزيل الملف...")
        file = update.message.document.get_file()
        pdf_path = f"temp_{update.message.message_id}.pdf"
        file.download(pdf_path)
        logger.info(f"تم تنزيل الملف: {pdf_path}")
        
        update.message.reply_text("⏳ جاري التحويل...")
        
        # رفع الملف إلى FreeConvert
        logger.info("جاري رفع الملف إلى FreeConvert...")
        task_id = upload_file(pdf_path)
        logger.info(f"تم رفع الملف. معرف المهمة: {task_id}")
        
        # بدء التحويل
        logger.info("جاري بدء عملية التحويل...")
        convert_pdf_to_docx(task_id)
        logger.info("تم بدء عملية التحويل.")
        
        # انتظار اكتمال التحويل
        logger.info("جاري الانتظار حتى اكتمال التحويل...")
        download_url = check_conversion_status(task_id)
        logger.info(f"تم اكتمال التحويل. رابط التنزيل: {download_url}")
        
        # تنزيل الملف المحوّل
        logger.info("جاري تنزيل الملف المحوّل...")
        docx_path = f"converted_{update.message.message_id}.docx"
        download_file(download_url, docx_path)
        logger.info(f"تم تنزيل الملف المحوّل: {docx_path}")
        
        # إرسال الملف المحوّل
        logger.info("جاري إرسال الملف المحوّل...")
        update.message.reply_document(
            document=open(docx_path, 'rb'),
            filename='converted.docx'
        )
        logger.info("تم إرسال الملف المحوّل.")
        
        # تنظيف الملفات المؤقتة
        logger.info("جاري تنظيف الملفات المؤقتة...")
        os.remove(pdf_path)
        os.remove(docx_path)
        logger.info("تم تنظيف الملفات المؤقتة.")
        
    except Exception as e:
        logger.error(f"حدث خطأ: {e}", exc_info=True)
        update.message.reply_text("❌ حدث خطأ أثناء التحويل. يرجى المحاولة لاحقًا.")

def upload_file(file_path: str) -> str:
    """رفع الملف إلى FreeConvert"""
    response = requests.get(
        "https://api.freeconvert.com/v1/process/import/upload",
        headers=headers
    )
    if response.status_code != 200:
        raise Exception(f"فشل في الحصول على رابط الرفع: {response.status_code} - {response.text}")
    
    upload_data = response.json()
    
    with open(file_path, 'rb') as f:
        upload_response = requests.post(
            upload_data['url'],
            files={'file': f},
            data=upload_data['parameters']
        )
    
    if upload_response.status_code != 200:
        raise Exception(f"فشل في رفع الملف: {upload_response.status_code} - {upload_response.text}")
    
    return upload_data['id']

def convert_pdf_to_docx(task_id: str):
    """بدء عملية التحويل"""
    response = requests.post(
        f"https://api.freeconvert.com/v1/convert/pdf/to/docx/{task_id}",
        headers=headers
    )
    if response.status_code != 200:
        raise Exception(f"فشل في بدء التحويل: {response.status_code} - {response.text}")

def check_conversion_status(task_id: str) -> str:
    """متابعة حالة التحويل"""
    while True:
        response = requests.get(
            f"https://api.freeconvert.com/v1/process/{task_id}",
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"فشل في التحقق من حالة التحويل: {response.status_code} - {response.text}")
        
        data = response.json()
        if data['status'] == 'completed':
            return data['output']['url']
        elif data['status'] == 'failed':
            raise Exception("فشل التحويل: " + data.get('message', 'Unknown error'))
        
        time.sleep(2)

def download_file(url: str, output_path: str):
    """تنزيل الملف المحوّل"""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"فشل في تنزيل الملف: {response.status_code} - {response.text}")
    
    with open(output_path, 'wb') as f:
        f.write(response.content)

def main():
    # إنشاء Updater وتمرير التوكن
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # تسجيل الـ handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
