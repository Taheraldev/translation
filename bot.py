import os
import time
import requests
import groupdocs_translation_cloud
from pdf2docx import Converter
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# 🔹 بيانات المصادقة API الخاصة بـ GroupDocs
GROUPDOCS_CLIENT_ID = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
GROUPDOCS_CLIENT_SECRET = "20c8c4f0947d9901282ee3576ec31535"

# 🔹 إعداد الـ API
configuration = groupdocs_translation_cloud.Configuration()
configuration.app_sid = GROUPDOCS_CLIENT_ID
configuration.api_key["apiKey"] = GROUPDOCS_CLIENT_SECRET

api_client = groupdocs_translation_cloud.ApiClient(configuration)

# 🔹 الحصول على Access Token
def get_access_token():
    auth_url = "https://api.groupdocs.cloud/connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": GROUPDOCS_CLIENT_ID,
        "client_secret": GROUPDOCS_CLIENT_SECRET
    }
    response = requests.post(auth_url, headers=headers, data=data)
    response_data = response.json()
    
    if "access_token" in response_data:
        return response_data["access_token"]
    else:
        raise Exception(f"❌ فشل الحصول على Access Token: {response_data}")

# 🔹 تحويل PDF إلى DOCX
def convert_pdf_to_docx(pdf_path, docx_path):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()

# 🔹 استقبال ملفات PDF
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document

    # ✅ التأكد من أن الملف PDF
    if file.mime_type != "application/pdf":
        update.message.reply_text("❌ الرجاء إرسال ملف PDF فقط.")
        return

    # ✅ التحقق من حجم الملف (1MB حد أقصى)
    if file.file_size > 1_000_000:
        update.message.reply_text("❌ حجم الملف كبير جدًا! الرجاء إرسال ملف أقل من 1MB.")
        return

    file_path = f"{file.file_id}.pdf"
    docx_path = f"{file.file_id}.docx"

    # 🔹 تحميل الملف من تيليجرام
    pdf_file = context.bot.get_file(file.file_id)
    pdf_file.download(file_path)

    # 🔹 تحويل PDF إلى DOCX
    convert_pdf_to_docx(file_path, docx_path)

    update.message.reply_text("⏳ يتم الآن إرسال الملف للترجمة...")

    # 🔹 الحصول على Access Token
    try:
        access_token = get_access_token()
    except Exception as e:
        update.message.reply_text(f"❌ فشل المصادقة: {str(e)}")
        return

    # 🔹 إعداد طلب الترجمة
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    request_body = {
        "sourceLanguage": "en",
        "targetLanguages": ["ar"],
        "format": "Docx",
        "outputFormat": "Docx",
        "name": docx_path,
        "folder": "",
        "savefile": f"translated_{file.file_id}.docx",
        "masters": False,
        "elements": []
    }

    # 🔹 إرسال الملف للترجمة
    try:
        translate_url = "https://api.groupdocs.cloud/v2.0/translation/document"
        response = requests.post(translate_url, headers=headers, json=request_body)
        response_data = response.json()

        if "requestId" not in response_data:
            update.message.reply_text(f"❌ فشل إرسال الملف للترجمة: {response_data}")
            return

        request_id = response_data["requestId"]
        update.message.reply_text("🚀 الترجمة جارية... الرجاء الانتظار.")

        # 🔹 متابعة حالة الترجمة
        translated_doc_url = None
        while True:
            status_url = f"https://api.groupdocs.cloud/v2.0/translation/document/{request_id}"
            status_response = requests.get(status_url, headers=headers).json()
            
            if status_response.get("status") == "Completed":
                translated_doc_url = status_response.get("url")
                break
            elif status_response.get("status") == "Failed":
                update.message.reply_text("❌ فشلت الترجمة!")
                return

            time.sleep(3)  # الانتظار قبل الاستعلام مرة أخرى

        # 🔹 تحميل الملف المترجم
        translated_docx_path = f"translated_{file.file_id}.docx"
        file_response = requests.get(translated_doc_url, headers={"Accept": "application/octet-stream"})
        with open(translated_docx_path, "wb") as f:
            f.write(file_response.content)

        # 🔹 إرسال الملف المترجم للمستخدم
        update.message.reply_document(document=open(translated_docx_path, "rb"), filename="Translated.docx")
        update.message.reply_text("✅ تم ترجمة الملف بنجاح!")

    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {str(e)}")

# 🔹 تشغيل البوت
def main():
    TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
