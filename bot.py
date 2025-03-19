import os
import logging
import base64
import requests
import time
from telegram.ext import Updater, MessageHandler, Filters

# إعدادات Smartcat
SMARTCAT_USERNAME = "acidgreen5@tmarapten.com"  # استبدله باسم المستخدم الحقيقي
SMARTCAT_PASSWORD = "Tahertrans2025@@"  # استبدله بكلمة المرور الحقيقية
BASE_URL = "https://smartcat.ai/api/integration/v1/"  # للسيرفر الأوروبي
PROJECT_ID = "21355320-aee6-4b65-966f-a810e802b81a"  # استبدل بمعرف المشروع

# توليد مفتاح التوثيق Base64
auth_string = f"{SMARTCAT_USERNAME}:{SMARTCAT_PASSWORD}"
encoded_auth = base64.b64encode(auth_string.encode()).decode()

headers = {
    "Authorization": f"Key {encoded_auth}",
    "Accept": "application/json"
}

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def handle_pdf(update, context):
    user = update.message.from_user
    temp_pdf = None
    translated_file = None

    try:
        # تنزيل الملف
        file = update.message.document.get_file()
        temp_pdf = f"temp_{user.id}.pdf"
        file.download(temp_pdf)
        
        # رفع الملف إلى Smartcat
        update.message.reply_text("☁️ جاري رفع الملف...")
        document_id = upload_to_smartcat(temp_pdf)
        
        # بدء الترجمة
        update.message.reply_text("🔄 بدأت الترجمة...")
        start_translation(document_id)
        
        # تنزيل الملف المترجم
        update.message.reply_text("⏳ جاري التحميل...")
        translated_file = get_translated_file(document_id)
        
        # إرسال الملف
        update.message.reply_document(
            document=open(translated_file, "rb"),
            caption="✅ تمت الترجمة"
        )

    except Exception as e:
        update.message.reply_text(f"❌ خطأ: {str(e)}")
        
    finally:
        # تنظيف الملفات المؤقتة
        if temp_pdf and os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        if translated_file and os.path.exists(translated_file):
            os.remove(translated_file)

def upload_to_smartcat(file_path):
    # إنشاء مستند جديد في المشروع
    url = f"{BASE_URL}project/{PROJECT_ID}/document"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    document_id = response.json()["id"]
    upload_url = response.json()["uploadUrl"]
    
    # رفع المحتوى الفعلي
    with open(file_path, "rb") as f:
        upload_response = requests.put(upload_url, data=f)
        upload_response.raise_for_status()
    
    return document_id

def start_translation(document_id):
    url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/start"
    response = requests.post(url, headers=headers)
    response.raise_for_status()

def get_translated_file(document_id):
    # الانتظار حتى تكتمل الترجمة
    while True:
        status_url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/status"
        response = requests.get(status_url, headers=headers)
        status = response.json().get("status")
        
        if status == "completed":
            break
        elif status == "failed":
            raise Exception("فشلت الترجمة")
        
        time.sleep(10)  # تقليل عدد الطلبات لتجنب تجاوز الحد المسموح

    # تنزيل الملف المترجم
    download_url = f"{BASE_URL}project/{PROJECT_ID}/document/{document_id}/download"
    response = requests.get(download_url, headers=headers)
    response.raise_for_status()
    
    # حفظ الملف مؤقتًا
    file_path = f"translated_{document_id}.docx"
    with open(file_path, "wb") as f:
        f.write(response.content)
    
    return file_path

if __name__ == "__main__":
    # استبدل 'YOUR_BOT_TOKEN' بتوكن البوت الخاص بك
    updater = Updater("5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_pdf))
    updater.start_polling()
    updater.idle()
