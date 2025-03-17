import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.pdf_file_request import PdfFileRequest
from groupdocs_translation_cloud.rest import ApiException

# إعداد تسجيل الأخطاء
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# إعداد توكن البوت و GroupDocs
TELEGRAM_BOT_TOKEN = "5146976580:AAGnkVkJsI37f8rWXOUjHcbZYoMIvhWHOW8"  # استبدل بتوكن البوت الخاص بك
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3NDIxOTY0ODIsImV4cCI6MTc0MjIwMDA4MiwiaXNzIjoiaHR0cHM6Ly9hcGkuZ3JvdXBkb2NzLmNsb3VkIiwiYXVkIjpbImh0dHBzOi8vYXBpLmdyb3VwZG9jcy5jbG91ZC9yZXNvdXJjZXMiLCJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl0sImNsaWVudF9pZCI6ImE5MWE2YWQxLTc2MzctNGU2NS1iNzkzLTQxYWY1NTQ1MDgwNyIsImNsaWVudF9kZWZhdWx0X3N0b3JhZ2UiOiJhNzA4ZTFhYS1hMjI1LTQxNjMtYWEwNS02YzE3MDU3NTUxMzQiLCJjbGllbnRfaWRlbnRpdHlfdXNlcl9pZCI6IjEwMjY4OTYiLCJzY29wZSI6WyJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl19.TiEtrBftDVwZWPugwZeX6A3Bsd8OcmlxduIVdJu-cWtu3R73DbKe39JeAh4gdYxPpVM5QbCmGUbXZL7XjDBmtRmY8q-V9f4XpBAH18cyv8NuNUyxvNPS1j17VK46IpP7rkv7WNOBpCb-BZbUZX4VPQlftGxmiiAxeT9Imq4_2I5egdbhkUCxqkki764jWlTSTDlGrgc5JR2SnUMAsGekxw7lXHXZgndeAPUmtV4BLi6zsGQC83BkkVsKIm1i9oG5H2aBa3j95giwj-YkWlxmlneKlkkxYn4ThiNvrPYNIQE7TPGwgFqWjDqr0nxJq4pf6TfYCAEjhkLIHg1oR4dxbg"  # استبدل بتوكن GroupDocs

# تكوين API لـ GroupDocs
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = ACCESS_TOKEN
api_instance = groupdocs_translation_cloud.TranslationApi(groupdocs_translation_cloud.ApiClient(configuration))

# مجلد تخزين الملفات
DOWNLOAD_FOLDER = "./downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 📝 دالة بدء البوت
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 أهلاً بك! أرسل ملف PDF لترجمته.")

# 📥 دالة استقبال الملفات
def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    if not document.file_name.endswith(".pdf"):
        update.message.reply_text("❌ يجب إرسال ملف PDF فقط!")
        return

    file = context.bot.get_file(document.file_id)
    file_path = os.path.join(DOWNLOAD_FOLDER, document.file_name)
    file.download(file_path)

    update.message.reply_text("✅ تم تحميل الملف! ⏳ جارٍ الترجمة...")

    # ترجمة الملف
    translated_file_path = translate_pdf(file_path)

    if translated_file_path:
        update.message.reply_document(open(translated_file_path, "rb"), caption="✅ تم ترجمة الملف بنجاح!")
    else:
        update.message.reply_text("❌ حدث خطأ أثناء الترجمة.")

# 🔄 دالة ترجمة PDF عبر GroupDocs
def translate_pdf(pdf_path: str) -> str:
    try:
        pdf_request = PdfFileRequest(
            file=open(pdf_path, "rb"),
            source_language="en",
            target_language="ar"
        )
        response = api_instance.pdf_post(pdf_request)

        if response.status == "Ok":
            translated_file_path = pdf_path.replace(".pdf", "_translated.pdf")
            with open(translated_file_path, "wb") as f:
                f.write(response.file_content)
            return translated_file_path
    except ApiException as e:
        logging.error(f"❌ خطأ في API: {e}")
    return None

# ⚙️ تشغيل البوت
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
