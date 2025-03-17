from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import groupdocs_translation_cloud
from pdf2docx import Converter

# إعداد المصادقة الخاصة بـ GroupDocs API
GROUPDOCS_CLIENT_ID = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
GROUPDOCS_CLIENT_SECRET = "20c8c4f0947d9901282ee3576ec31535"

configuration = groupdocs_translation_cloud.Configuration()
configuration.api_key["apiKey"] = GROUPDOCS_CLIENT_SECRET
configuration.api_key["appSid"] = GROUPDOCS_CLIENT_ID

api_client = groupdocs_translation_cloud.ApiClient(configuration)
api_instance = groupdocs_translation_cloud.TranslationApi(api_client)

# دالة تحويل PDF إلى DOCX
def convert_pdf_to_docx(pdf_path, docx_path):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()

# دالة استقبال ملفات PDF
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if file.mime_type != "application/pdf":
        update.message.reply_text("❌ الرجاء إرسال ملف PDF فقط.")
        return

    file_path = f"{file.file_id}.pdf"
    docx_path = f"{file.file_id}.docx"

    # تحميل الملف
    pdf_file = context.bot.get_file(file.file_id)
    pdf_file.download(file_path)

    # تحويل PDF إلى DOCX
    convert_pdf_to_docx(file_path, docx_path)

    # إعداد طلب الترجمة
    request = groupdocs_translation_cloud.TextDocumentFileRequest(
        pair="en-ar",
        storage="First Storage",
        name=docx_path,
        savefile=f"translated_{file.file_id}.docx"
    )

    # إرسال الملف للترجمة
    response = api_instance.document_post(request)
    request_id = response.request_id
    update.message.reply_text(f"⏳ يتم الآن ترجمة الملف... الرجاء الانتظار.")

    # متابعة حالة الترجمة
    translated_doc_url = None
    while True:
        status_response = api_instance.document_request_id_get(request_id)
        if status_response.status == "Completed":
            translated_doc_url = status_response.url
            break

    # تحميل وإرسال الملف المترجم
    translated_docx_path = f"translated_{file.file_id}.docx"
    os.system(f"wget -O {translated_docx_path} {translated_doc_url}")

    update.message.reply_document(document=open(translated_docx_path, "rb"), filename="Translated.docx")

# تشغيل البوت
def main():
    TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
