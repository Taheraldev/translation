import os
import requests
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()
API_KEY = os.getenv('api_production_8c2dd4109244aa3e3b155ffb6f1c883fa6b37f62657a7834b9c3d4365b23d4a6.67dd34d41b1ec0ad5910e28c.67dd3566824532b94589fab6')
TELEGRAM_TOKEN = os.getenv('5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc')

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
        file = update.message.document.get_file()
        pdf_path = f"temp_{update.message.message_id}.pdf"
        file.download(pdf_path)
        
        update.message.reply_text("⏳ جاري التحويل...")
        
        # رفع الملف إلى FreeConvert
        task_id = upload_file(pdf_path)
        
        # بدء التحويل
        convert_pdf_to_docx(task_id)
        
        # انتظار اكتمال التحويل
        download_url = check_conversion_status(task_id)
        
        # تنزيل الملف المحوّل
        docx_path = f"converted_{update.message.message_id}.docx"
        download_file(download_url, docx_path)
        
        # إرسال الملف المحوّل
        update.message.reply_document(
            document=open(docx_path, 'rb'),
            filename='converted.docx'
        )
        
        # تنظيف الملفات المؤقتة
        os.remove(pdf_path)
        os.remove(docx_path)
        
    except Exception as e:
        logger.error(e)
        update.message.reply_text("❌ حدث خطأ أثناء التحويل. يرجى المحاولة لاحقًا.")

def upload_file(file_path: str) -> str:
    """رفع الملف إلى FreeConvert"""
    response = requests.get(
        "https://api.freeconvert.com/v1/process/import/upload",
        headers=headers
    )
    upload_data = response.json()
    
    with open(file_path, 'rb') as f:
        requests.post(
            upload_data['url'],
            files={'file': f},
            data=upload_data['parameters']
        )
    
    return upload_data['id']

def convert_pdf_to_docx(task_id: str):
    """بدء عملية التحويل"""
    response = requests.post(
        f"https://api.freeconvert.com/v1/convert/pdf/to/docx/{task_id}",
        headers=headers
    )
    return response.json()

def check_conversion_status(task_id: str) -> str:
    """متابعة حالة التحويل"""
    while True:
        response = requests.get(
            f"https://api.freeconvert.com/v1/process/{task_id}",
            headers=headers
        )
        data = response.json()
        if data['status'] == 'completed':
            return data['output']['url']
        time.sleep(2)

def download_file(url: str, output_path: str):
    """تنزيل الملف المحوّل"""
    response = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(response.content)

def main():
    # إنشاء Updater وتمرير التوكن
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

   
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
