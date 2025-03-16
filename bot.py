import os
import tempfile
import groupdocs_translation_cloud
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

# تكوين API
client_id = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
client_secret = "20c8c4f0947d9901282ee3576ec31535"
configuration = groupdocs_translation_cloud.Configuration(client_id, client_secret)
api = groupdocs_translation_cloud.TranslationApi.from_config(configuration)

def translate_pptx(input_path, output_path):
    try:
        settings = groupdocs_translation_cloud.TranslateDocument(
            source_language="en",
            target_language="ar",
            format="pptx",
            storage="",
            save_path=output_path
        )
        
        with open(input_path, 'rb') as f:
            response = api.translate_document(settings, f)
        
        return response.save_path
    
    except groupdocs_translation_cloud.ApiException as e:
        print(f"GroupDocs API Error: {e.reason}")
        raise

def handle_document(update: Update, context):
    try:
        document = update.message.document
        
        if document.mime_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            update.message.reply_text("❌ يرجى إرسال ملف PPTX فقط")
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            file = context.bot.get_file(document.file_id)
            input_path = os.path.join(tmp_dir, document.file_name)
            file.download(input_path)
            
            output_path = os.path.join(tmp_dir, "translated.pptx")
            translated_path = translate_pptx(input_path, output_path)
            
            with open(translated_path, 'rb') as f:
                update.message.reply_document(  # <-- تم إصلاح السطر هنا
                    document=f,
                    caption="تمت الترجمة بنجاح ✅",
                    filename=os.path.basename(translated_path)
                )  # <-- إضافة القوس المفقود
                
    except Exception as e:
        error_msg = f"فشلت العملية: {str(e)}"
        update.message.reply_text(error_msg)
        print(f"Error: {e}")

def main():
    updater = Updater("5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
