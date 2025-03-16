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
    # إنشاء طلب الترجمة مع رفع الملف تلقائيًا
    file_info = groupdocs_translation_cloud.FileInfo()
    file_info.file_path = input_path
    
    request = groupdocs_translation_cloud.TranslateDocumentRequest(
        file_info=file_info,
        target_language="ar",
        source_language="en",
        format="pptx",
        storage="",
        out_path=output_path
    )
    
    response = api.translate_document(request)
    return response.out_path

def handle_document(update: Update, context):
    document = update.message.document
    
    if document.mime_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        update.message.reply_text("يرجى إرسال ملف PPTX فقط.")
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
        with open(output_path, 'rb') as translated_file:
            update.message.reply_document(document=translated_file)

def main():
    updater = Updater("5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
