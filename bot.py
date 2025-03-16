import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import groupdocs_translation_cloud
from groupdocs_translation_cloud.rest import ApiException
import io
import time

# بيانات اعتماد تيليجرام و GroupDocs
TELEGRAM_BOT_TOKEN = '5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A'
CLIENT_ID = 'a0ab8978-a4d6-412d-b9cd-fbfcea706dee'
CLIENT_SECRET = '20c8c4f0947d9901282ee3576ec31535'

# إعداد GroupDocs Translation API
configuration = groupdocs_translation_cloud.Configuration(app_sid=APP_SID, api_key=API_KEY)
api_client = groupdocs_translation_cloud.ApiClient(configuration)
file_api = groupdocs_translation_cloud.FileApi(api_client)
translation_api = groupdocs_translation_cloud.TranslationApi(api_client)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي ملف PowerPoint (pptx) لترجمته من الإنجليزية إلى العربية.")

def translate_pptx(update, context):
    try:
        context.bot.send_message(chat_id=update.effective_chat.id, text="جاري بدء عملية الترجمة...")
        file = context.bot.get_file(update.message.document.file_id)
        file_data = file.download_as_bytearray()
        file_stream = io.BytesIO(file_data)

        # تحميل الملف إلى GroupDocs Cloud
        files = {"file": ("input.pptx", file_stream)}
        upload_response = file_api.upload_file("input.pptx", files)

        # إعداد طلب الترجمة
        settings = groupdocs_translation_cloud.TranslationOptions(
            source_language="en",
            target_languages=["ar"],
            storage_path="input.pptx",
            outputPath="translated.pptx"
        )
        translate_request = groupdocs_translation_cloud.TranslateDocumentRequest(settings)
        translation_api.translate_document(translate_request)

        # تنزيل الملف المترجم
        download_response = file_api.download_file("translated.pptx")
        translated_file = io.BytesIO(download_response)

        # إرسال الملف المترجم إلى المستخدم
        context.bot.send_document(chat_id=update.effective_chat.id, document=translated_file.getvalue(), filename="translated.pptx")
        context.bot.send_message(chat_id=update.effective_chat.id, text="تمت ترجمة الملف بنجاح.")

    except ApiException as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ أثناء الترجمة: {e}")
    except Exception as e:
         context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ غير معروف: {e}")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    document_handler = MessageHandler(Filters.document.mime_type("application/vnd.openxmlformats-officedocument.presentationml.presentation"), translate_pptx)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(document_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
