import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import groupdocs_translation_cloud
from groupdocs_translation_cloud.rest import ApiException
import time
from groupdocs_translation_cloud import TextRequest

# بيانات اعتماد تيليجرام و GroupDocs
TELEGRAM_BOT_TOKEN = '5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A'
CLIENT_ID = 'a0ab8978-a4d6-412d-b9cd-fbfcea706dee'
CLIENT_SECRET = '20c8c4f0947d9901282ee3576ec31535'

# إعداد GroupDocs Translation API
configuration = groupdocs_translation_cloud.Configuration(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
api_client = groupdocs_translation_cloud.ApiClient(configuration)
api = groupdocs_translation_cloud.TranslationApi(api_client)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي نصًا لترجمته من الإنجليزية إلى العربية.")

def translate_text(update, context):
    try:
        text = update.message.text
        text_request = TextRequest(
            source_language="en",
            target_languages=["ar"],
            texts=[text],
            origin="telegram_bot",
            contains_markdown=False
        )
        response = api.text_post(text_request)
        if response.status == 202:
            while True:
                status_response = api.text_request_id_get(response.id)
                if status_response.status == 200:
                    translation = status_response.translations["ar"][0]
                    context.bot.send_message(chat_id=update.effective_chat.id, text=translation)
                    break
                time.sleep(2)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="حدث خطأ أثناء الترجمة.")
    except ApiException as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ أثناء الترجمة: {e}")
    except Exception as e:
         context.bot.send_message(chat_id=update.effective_chat.id, text=f"حدث خطأ غير معروف: {e}")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    text_handler = MessageHandler(Filters.text & (~Filters.command), translate_text)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(text_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
