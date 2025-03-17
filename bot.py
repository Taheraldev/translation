import os
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.pdf_file_request import PdfFileRequest
from groupdocs_translation_cloud.rest import ApiException

# إعدادات التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# إعداد متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")  # ضع التوكن هنا أو احصل عليه من المتغير البيئي
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # ضع التوكن هنا أو احصل عليه من المتغير البيئي

# إعداد GroupDocs API
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = ACCESS_TOKEN

# دالة لمعالجة /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 أهلاً! أرسل ملف PDF (أقل من 1MB و 5 صفحات) للترجمة إلى العربية.")

# دالة لمعالجة الملفات المستلمة
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    file_size = file.file_size
    file_name = file.file_name

    # التحقق من أن الملف PDF
    if not file_name.endswith(".pdf"):
        update.message.reply_text("❌ الرجاء إرسال ملف PDF فقط.")
        return

    # التحقق من حجم الملف (1MB كحد أقصى)
    if file_size > 1_000_000:
        update.message.reply_text("❌ الحد الأقصى لحجم الملف هو 1MB.")
        return

    # تنزيل الملف
    file_path = f"downloads/{file.file_id}.pdf"
    os.makedirs("downloads", exist_ok=True)
    file.download(file_path)

    # إعداد API Client
    with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
        api_instance = groupdocs_translation_cloud.TranslationApi(api_client)

        # إعداد طلب الترجمة
        pdf_file_request = PdfFileRequest(
            source_language="en",
            target_languages=["ar"],
            original_file_name=file_name,
            url=None,
            savingMode="Files",
            outputFormat="pdf",
            preserveFormatting=True
        )

        try:
            # تنفيذ الترجمة
            api_response = api_instance.pdf_post(pdf_file_request=pdf_file_request)
            translated_file_url = api_response.result.urls[0]

            # تنزيل الملف المترجم
            translated_file_path = f"downloads/translated_{file.file_id}.pdf"
            os.system(f"wget -O {translated_file_path} {translated_file_url}")

            # إرسال الملف المترجم
            with open(translated_file_path, "rb") as translated_file:
                update.message.reply_document(document=InputFile(translated_file), caption="✅ تم ترجمة الملف بنجاح!")

        except ApiException as e:
            update.message.reply_text(f"❌ خطأ أثناء الترجمة: {e}")

# إعداد البوت
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
