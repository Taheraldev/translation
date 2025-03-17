import os
import time
import requests
import groupdocs_translation_cloud
from pdf2docx import Converter
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# 🔹 بيانات المصادقة API الخاصة بـ GroupDocs
CLIENT_ID = "a91a6ad1-7637-4e65-b793-41af55450807"
CLIENT_SECRET = "2d0c949f2cc2d12010f5427e6c1dc4da"

# 🔹 دالة لجلب Access Token
def get_access_token():
    url = "https://api.groupdocs.cloud/connect/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"❌ فشل طلب المصادقة! كود الاستجابة: {response.status_code} - الرد: {response.text}")

# 🔹 الحصول على التوكن
ACCESS_TOKEN = get_access_token()

# 🔹 تهيئة API Client
configuration = groupdocs_translation_cloud.Configuration()
configuration.access_token = ACCESS_TOKEN
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
    convert_pdf_to_docx(file_path, docx_path)

    update.message.reply_text("⏳ يتم الآن إرسال الملف للترجمة...")

    # 🔹 إعداد طلب الترجمة
    request = groupdocs_translation_cloud.TextDocumentFileRequest(
        source_language="en",
        target_languages=["ar"],
        format="Docx",
        output_format="Docx",
        name=docx_path,
        folder="",
        savefile=f"translated_{file.file_id}.docx",
        masters=False,
        elements=[]
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
    TOKEN = "5146976580:AAHc3N58Bbxh1-D2ydnA-BNlLmhXJ5kl1c0"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
