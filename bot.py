import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# إعدادات Smartcat
SMARTCAT_API_KEY = '2_FwEmd5QMpKxDbHnNnwydzEL3o'  # استبدل بمفتاح API الخاص بك
PROJECT_ID = '21355320-aee6-4b65-966f-a810e802b81a'  # استبدل بمعرف المشروع الخاص بك
BASE_URL = 'https://smartcat.com/api/integration/v1/'

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

headers = {
    'Authorization': f'Bearer {SMARTCAT_API_KEY}',
    'Accept': 'application/json'
}

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    temp_pdf = None
    translated_file = None  # تعريف المتغير مسبقًا

    try:
        # تنزيل الملف
        file = await update.message.document.get_file()
        temp_pdf = f"temp_{user.id}.pdf"
        await file.download_to_drive(temp_pdf)
        
        # رفع الملف إلى Smartcat
        await update.message.reply_text("☁️ جاري رفع الملف إلى Smartcat...")
        document_id = await upload_to_smartcat(temp_pdf)
        
        # بدء الترجمة
        await update.message.reply_text("🔄 بدأت عملية الترجمة...")
        await start_translation(document_id)
        
        # الحصول على الملف المترجم
        await update.message.reply_text("⏳ جاري تحميل الملف المترجم...")
        translated_file = await get_translated_file(document_id)
        
        # إرسال الملف المترجم
        await update.message.reply_document(
            document=open(translated_file, 'rb'),
            caption="✅ تمت الترجمة بنجاح"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")
    finally:
        # تنظيف الملفات المؤقتة
        if temp_pdf and os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        if translated_file and os.path.exists(translated_file):
            os.remove(translated_file)

async def upload_to_smartcat(file_path):
    url = f"{BASE_URL}project/create"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    document_id = response.json()['id']
    upload_url = response.json()['uploadUrl']
    
    with open(file_path, 'rb') as f:
        upload_response = requests.put(upload_url, data=f)
        upload_response.raise_for_status()
    
    return document_id

async def start_translation(document_id):
    url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/start"
    response = requests.post(url, headers=headers)
    response.raise_for_status()

async def get_translated_file(document_id):
    # الحصول على حالة الترجمة
    status_url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/status"
    while True:
        status_response = requests.get(status_url, headers=headers)
        status = status_response.json().get('status')
        
        if status == 'completed':
            break
        elif status == 'failed':
            raise Exception("فشلت عملية الترجمة")
        
        await asyncio.sleep(10)  # انتظار 10 ثواني قبل التحقق مرة أخرى
    
    # تنزيل الملف المترجم
    download_url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/download"
    file_response = requests.get(download_url, headers=headers)
    file_response.raise_for_status()
    
    file_path = f"translated_{document_id}.docx"
    with open(file_path, 'wb') as f:
        f.write(file_response.content)
    
    return file_path

if __name__ == '__main__':
    application = Application.builder().token('5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc').build()
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.run_polling()
