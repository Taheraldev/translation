from telegram.ext import Updater, MessageHandler, Filters
from telegram import Update
import requests
import os

# إعدادات Smartcat
SMARTCAT_API_KEY = '2_FwEmd5QMpKxDbHnNnwydzEL3o'
PROJECT_ID = '21355320-aee6-4b65-966f-a810e802b81a'
BASE_URL = 'https://smartcat.com/api/integration/v1/'

def handle_pdf(update, context):
    user = update.message.from_user
    try:
        # تنزيل الملف
        file = update.message.document.get_file()
        temp_pdf = f"temp_{user.id}.pdf"
        file.download(temp_pdf)
        
        # رفع الملف إلى Smartcat
        document_id = upload_to_smartcat(temp_pdf)
        
        # بدء الترجمة
        start_translation(document_id)
        
        # الحصول على الملف المترجم
        translated_file = get_translated_file(document_id)
        update.message.reply_document(
            document=open(translated_file, 'rb'),
            caption="✅ تمت الترجمة بنجاح"
        )
        
    except Exception as e:
        update.message.reply_text(f"❌ خطأ: {str(e)}")
    finally:
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        if os.path.exists(translated_file):
            os.remove(translated_file)

def upload_to_smartcat(file_path):
    url = f"{BASE_URL}project/{PROJECT_ID}/document"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    document_id = response.json()['id']
    upload_url = response.json()['uploadUrl']
    
    with open(file_path, 'rb') as f:
        upload_response = requests.put(upload_url, data=f)
        upload_response.raise_for_status()
    
    return document_id

def start_translation(document_id):
    url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/start"
    response = requests.post(url, headers=headers)
    response.raise_for_status()

def get_translated_file(document_id):
    doc_url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}"
    response = requests.get(doc_url, headers=headers)
    download_url = response.json()['translatedFileUrl']
    
    file_response = requests.get(download_url)
    file_path = f"translated_{document_id}.docx"
    
    with open(file_path, 'wb') as f:
        f.write(file_response.content)
    
    return file_path

if __name__ == '__main__':
    updater = Updater("5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))
    updater.start_polling()
    updater.idle()
