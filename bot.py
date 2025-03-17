import os
import time
import requests
import groupdocs_translation_cloud
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# ==============================
# إعداد بيانات المصادقة
# ==============================
CLIENT_ID = "a91a6ad1-7637-4e65-b793-41af55450807"         # استبدل بـ Client ID الخاص بك
CLIENT_SECRET = "2d0c949f2cc2d12010f5427e6c1dc4da" # استبدل بـ Client Secret الخاص بك
TELEGRAM_BOT_TOKEN = "5146976580:AAHMM1HhJb-S0rD5AiEUjC2547aeqG0z2Uw"  # استبدل بتوكن بوت تيليجرام

# دالة الحصول على Access Token من GroupDocs
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

ACCESS_TOKEN = get_access_token()

# ==============================
# إعداد Translation API (GroupDocs Translation Cloud)
# ==============================
translation_configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
translation_configuration.access_token = ACCESS_TOKEN
translation_api_client = groupdocs_translation_cloud.ApiClient(translation_configuration)
translation_api_instance = groupdocs_translation_cloud.TranslationApi(translation_api_client)

# ==============================
# دالة رفع الملف إلى التخزين السحابي باستخدام REST API (GroupDocs Storage API)
# ==============================
def upload_file_to_storage(local_file_path, remote_file_path):
    # نستخدم اسم الملف فقط بدون مجلد، مثل "filename.pdf"
    upload_url = f"https://api.groupdocs.cloud/v2.0/storage/file/{remote_file_path}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/octet-stream"
    }
    with open(local_file_path, "rb") as f:
        file_data = f.read()
    response = requests.put(upload_url, headers=headers, data=file_data)
    if response.status_code == 200:
        return remote_file_path
    else:
        raise Exception(f"❌ فشل رفع الملف: {response.status_code} - {response.text}")

# ==============================
# دالة التعامل مع ملف PDF المرسل عبر تيليجرام
# ==============================
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document

    # التأكد من أن الملف من نوع PDF
    if file.mime_type != "application/pdf":
        update.message.reply_text("❌ الرجاء إرسال ملف PDF فقط.")
        return

    # التحقق من حجم الملف (مثال: أقل من 1MB)
    if file.file_size > 1_000_000:
        update.message.reply_text("❌ حجم الملف كبير جدًا! الرجاء إرسال ملف أقل من 1MB.")
        return

    # تنزيل الملف محليًا
    local_pdf_path = f"{file.file_id}.pdf"
    pdf_file = context.bot.get_file(file.file_id)
    pdf_file.download(local_pdf_path)

    update.message.reply_text("⏳ جاري رفع الملف إلى التخزين السحابي...")

    # استخدام اسم الملف فقط بدون مجلد
    remote_file_path = os.path.basename(local_pdf_path)
    try:
        upload_file_to_storage(local_pdf_path, remote_file_path)
    except Exception as e:
        update.message.reply_text(f"❌ خطأ أثناء رفع الملف: {str(e)}")
        return

    update.message.reply_text("⏳ جاري إرسال الملف للترجمة...")

    # إعداد طلب الترجمة باستخدام PdfFileRequest
    try:
        pdf_file_request = groupdocs_translation_cloud.PdfFileRequest()
        pdf_file_request.sourceLanguage = "en"
        pdf_file_request.targetLanguages = ["ar"]
        pdf_file_request.originalFileName = file.file_name  # اسم الملف الأصلي كما أُرسل من المستخدم
        pdf_file_request.url = remote_file_path           # اسم الملف الذي رفعناه (يُستخدم مع التخزين الافتراضي)
        pdf_file_request.origin = "Telegram"
        pdf_file_request.savingMode = "Files"
        pdf_file_request.outputFormat = "Pdf"
        pdf_file_request.preserveFormatting = True
        pdf_file_request.pages = []  # ترجمة جميع الصفحات

        # إرسال طلب الترجمة عبر endpoint pdf_post
        translation_response = translation_api_instance.pdf_post(pdf_file_request=pdf_file_request)

        # معالجة الاستجابة
        if translation_response.message:
            update.message.reply_text(f"✅ تمت الترجمة: {translation_response.message}")
        else:
            update.message.reply_text("✅ تمت الترجمة بنجاح!")
    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ أثناء الترجمة: {str(e)}")

# ==============================
# تشغيل بوت تيليجرام
# ==============================
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
