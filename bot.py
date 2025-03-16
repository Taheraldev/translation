import os
import tempfile
import groupdocs_translation_cloud
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

# تكوين GroupDocs API
client_id = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
client_secret = "20c8c4f0947d9901282ee3576ec31535"
configuration = groupdocs_translation_cloud.Configuration(client_id, client_secret)
api = groupdocs_translation_cloud.TranslationApi(groupdocs_translation_cloud.ApiClient(configuration))

def translate_pptx(input_path, output_path):
    # رفع الملف باستخدام الطريقة المباشرة
    with open(input_path, 'rb') as file_stream:
        upload_result = api.upload_file(file_stream, os.path.basename(input_path))
    
    # تكوين طلب الترجمة
    request = groupdocs_translation_cloud.TranslateDocumentRequest(
        name=os.path.basename(input_path),
        target_language="ar",
        source_language="en",
        format="pptx",
        storage="",
        out_path=output_path
    )
    
    # تنفيذ الترجمة
    response = api.translate_document(request)
    return response.out_path

def handle_document(update: Update, context):
    try:
        document = update.message.document
        
        if document.mime_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            update.message.reply_text("❗ يرجى إرسال ملف PPTX فقط")
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            # تنزيل الملف
            file = context.bot.get_file(document.file_id)
            input_path = os.path.join(tmp_dir, document.file_name)
            file.download(input_path)
            
            # الترجمة
            output_path = os.path.join(tmp_dir, "translated.pptx")
            translated_path = translate_pptx(input_path, output_path)
            
            # إرسال الملف المترجم
            with open(translated_path, 'rb') as translated_file:
                update.message.reply_document(
                    document=translated_file,
                    caption="✅ تمت الترجمة بنجاح"
                )
                
    except Exception as e:
        error_msg = f"❌ حدث خطأ: {str(e)}"
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
