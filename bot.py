import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models import PdfFileRequest

# استبدل هذه القيم بالقيم الخاصة بك
TELEGRAM_BOT_TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
GROUPDOCS_CLIENT_ID = "a91a6ad1-7637-4e65-b793-41af55450807"
GROUPDOCS_CLIENT_SECRET = "2d0c949f2cc2d12010f5427e6c1dc4da"

# تهيئة GroupDocs Translation Cloud
configuration = groupdocs_translation_cloud.Configuration(client_id=GROUPDOCS_CLIENT_ID, client_secret=GROUPDOCS_CLIENT_SECRET)
api_client = groupdocs_translation_cloud.ApiClient(configuration)
translation_api = groupdocs_translation_cloud.TranslationApi(api_client)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي ملف PDF لترجمته من الإنجليزية إلى العربية.")

def handle_document(update, context):
    try:
        file_id = update.message.document.file_id
        file_info = context.bot.get_file(file_id)
        file_path = file_info.file_path
        file_name = update.message.document.file_name

        # تنزيل الملف
        context.bot.send_message(chat_id=update.effective_chat.id, text="جاري تنزيل الملف...")
        file = context.bot.get_file(file_id)
        downloaded_file = file.download_as_bytearray()

        # تهيئة طلب GroupDocs Translation Cloud
        pdf_file_request = PdfFileRequest(
            source_path=file_name,
            source_language="en",
            target_languages=["ar"],  # استخدام قائمة للغات الهدف
            output_format="pdf"  # تحديد تنسيق الملف الناتج
        )

        # ترجمة الملف
        context.bot.send_message(chat_id=update.effective_chat.id, text="جاري ترجمة الملف...")
        translated_status = translation_api.pdf_post(pdf_file_request=pdf_file_request)

        # استخراج الملف المترجم من الاستجابة
        translated_file_bytes = translated_status.result.read() # استخراج البايتات من الاستجابه

        # إرسال الملف المترجم
        context.bot.send_document(chat_id=update.effective_chat.id, document=translated_file_bytes, filename=f"translated_{file_name}")

    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ: {e}")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
