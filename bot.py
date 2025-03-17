import os
import time
import requests
import groupdocs_translation_cloud
from pdf2docx import Converter
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# 🔹 بيانات المصادقة الخاصة بـ GroupDocs
GROUPDOCS_CLIENT_ID = "YOUR_CLIENT_ID"
GROUPDOCS_CLIENT_SECRET = "YOUR_CLIENT_SECRET"

# 🔹 إعداد GroupDocs API
def get_access_token():
    auth_url = "https://api.groupdocs.cloud/connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": GROUPDOCS_CLIENT_ID,
        "client_secret": GROUPDOCS_CLIENT_SECRET
    }
    response = requests.post(auth_url, headers=headers, data=data)

    print(f"🔹 Auth Response Status Code: {response.status_code}")
    print(f"🔹 Auth Response Text: {response.text}")

    try:
        response_data = response.json()
    except Exception as e:
        raise Exception(f"❌ فشل تحليل JSON: {str(e)} - الرد: {response.text}")

    if "access_token" in response_data:
        return response_data["access_token"]
    else:
        raise Exception(f"❌ فشل الحصول على Access Token: {response_data}")

access_token = get_access_token()

configuration = groupdocs_translation_cloud.Configuration()
configuration.access_token = access_token
api_client = groupdocs_translation_cloud.ApiClient(configuration)
api_instance = groupdocs_translation_cloud.TranslationApi(api_client)

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
    update.message.reply_text("⏳ يتم الآن تحويل الملف إلى صيغة قابلة للترجمة...")
    convert_pdf_to_docx(file_path, docx_path)

    update.message.reply_text("⏳ يتم الآن إرسال الملف للترجمة...")

    # 🔹 إعداد طلب الترجمة
    request = groupdocs_translation_cloud.TextDocumentFileRequest(
        sourceLanguage="en",
        targetLanguages=["ar"],
        format="Docx",
        name=docx_path,
        folder="",
        savefile=f"translated_{file.file_id}.docx"
    )

    # 🔹 إرسال الملف للترجمة
    try:
        response = api_instance.document_post(request)
        request_id = response.request_id
        update.message.reply_text("🚀 الترجمة جارية... الرجاء الانتظار.")

        # 🔹 متابعة حالة الترجمة
        translated_doc_url = None
        while True:
            status_response = api_instance.document_request_id_get(request_id)
            if status_response.status == "Completed":
                translated_doc_url = status_response.url
                break
            time.sleep(3)  # الانتظار قبل الاستعلام مرة أخرى

        # 🔹 تحميل الملف المترجم
        translated_docx_path = f"translated_{file.file_id}.docx"
        response = requests.get(translated_doc_url)
        with open(translated_docx_path, "wb") as f:
            f.write(response.content)

        # 🔹 إرسال الملف المترجم للمستخدم
        update.message.reply_document(document=open(translated_docx_path, "rb"), filename="Translated.docx")
        update.message.reply_text("✅ تم ترجمة الملف بنجاح!")

    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {str(e)}")

# 🔹 تشغيل البوت
def main():
    TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
