import os
import requests
import logging
from io import BytesIO
from telegram import Update, InputFile
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

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"مرحبًا {user.first_name}! أرسل ملف PDF لتحويله إلى DOCX.")

def handle_pdf(update: Update, context: CallbackContext):
    try:
        # تنزيل الملف المؤقت
        file = update.message.document.get_file()
        file_stream = BytesIO()
        file.download(out=file_stream)
        file_stream.seek(0)
        
        update.message.reply_text("⏳ جاري التحويل...")

        # إنشاء مهمة التحويل
        job_payload = {
            "tasks": {
                "import-1": {"operation": "import/upload", "filename": "input.pdf"},
                "convert-1": {
                    "operation": "convert",
                    "input": "import-1",
                    "input_format": "pdf",
                    "output_format": "docx"
                },
                "export-1": {"operation": "export/url", "input": ["convert-1"]}
            }
        }

        # إنشاء المهمة
        response = requests.post(
            "https://api.freeconvert.com/v1/process/jobs",
            headers=headers,
            json=job_payload
        )
        
        if response.status_code != 201:
            raise Exception(f"خطأ في إنشاء المهمة: {response.text}")

        job_data = response.json()
        job_id = job_data['id']
        upload_url = job_data['tasks']['import-1']['result']['form']['url']
        upload_fields = job_data['tasks']['import-1']['result']['form']['parameters']

        # رفع الملف مباشرة من الذاكرة
        files = {'file': ('input.pdf', file_stream)}
        upload_response = requests.post(upload_url, files=files, data=upload_fields)
        
        if upload_response.status_code != 200:
            raise Exception(f"خطأ في الرفع: {upload_response.text}")

        # متابعة حالة التحويل
        while True:
            status_response = requests.get(
                f"https://api.freeconvert.com/v1/process/{job_id}",
                headers=headers
            )
            status_data = status_response.json()
            
            if status_data['status'] == 'completed':
                download_url = status_data['tasks']['export-1']['result']['files'][0]['url']
                break
            elif status_data['status'] == 'failed':
                raise Exception("فشل التحويل: " + status_data.get('message', 'Unknown error'))
            time.sleep(5)

        # تنزيل وإرسال الملف مباشرة من الذاكرة
        docx_response = requests.get(download_url)
        docx_file = BytesIO(docx_response.content)
        docx_file.name = 'converted.docx'
        
        update.message.reply_document(
            document=InputFile(docx_file),
            caption="تم التحويل بنجاح 🎉"
        )

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        update.message.reply_text("❌ حدث خطأ أثناء التحويل. يرجى المحاولة لاحقًا.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
