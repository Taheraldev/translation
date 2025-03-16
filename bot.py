import os
import tempfile
import groupdocs_translation_cloud
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

# تكوين API
client_id = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
client_secret = "20c8c4f0947d9901282ee3576ec31535"
configuration = groupdocs_translation_cloud.Configuration(client_id, client_secret)
api_client = groupdocs_translation_cloud.ApiClient(configuration)
api = groupdocs_translation_cloud.DocumentApi(api_client)  # <-- تغيير الـ API هنا

def translate_pptx(input_path, output_path):
    try:
        # رفع الملف وتكوين الإعدادات
        upload_request = groupdocs_translation_cloud.UploadDocumentRequest(
            file=open(input_path, 'rb'),
            target_languages=["ar"],
            source_language="en",
            format="pptx",
            storage="",
            out_path=output_path
        )
        
        # إرسال الطلب
        response = api.translate_document(upload_request)
        return response.out_path
    
    except Exception as e:
        print(f"GroupDocs Error: {str(e)}")
        raise

def handle_document(update: Update, context):
    try:
        document = update.message.document
        
        if document.mime_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            update.message.reply_text("❌ يرجى إرسال ملف PPTX فقط")
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            # تنزيل الملف
            file = context.bot.get_file(document.file_id)
            input_path = os.path.join(tmp_dir, document.file_name)
            file.download(input_path)
            
            # الترجمة
            output_path = os.path.join(tmp_dir, "translated.pptx")
            translated_path = translate_pptx(input_path, output_path)
            
            # إرسال النتيجة
            with open(translated_path, 'rb') as f:
                update.message.reply_document(
                    document=f,
                    caption="تمت الترجمة بنجاح ✅",
                    filename=os.path.basename(translated_path)
                )
                
    except Exception as e:
        error_msg = f"فشلت العملية: {str(e)}"
        update.message.reply_text(error_msg)
        print(f"Error Trace: {str(e)}")

def main():
    updater = Updater("import os
import tempfile
import groupdocs_translation_cloud
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters

# تكوين API
client_id = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
client_secret = "20c8c4f0947d9901282ee3576ec31535"
configuration = groupdocs_translation_cloud.Configuration(client_id, client_secret)
api_client = groupdocs_translation_cloud.ApiClient(configuration)
api = groupdocs_translation_cloud.DocumentApi(api_client)  # <-- تغيير الـ API هنا

def translate_pptx(input_path, output_path):
    try:
        # رفع الملف وتكوين الإعدادات
        upload_request = groupdocs_translation_cloud.UploadDocumentRequest(
            file=open(input_path, 'rb'),
            target_languages=["ar"],
            source_language="en",
            format="pptx",
            storage="",
            out_path=output_path
        )
        
        # إرسال الطلب
        response = api.translate_document(upload_request)
        return response.out_path
    
    except Exception as e:
        print(f"GroupDocs Error: {str(e)}")
        raise

def handle_document(update: Update, context):
    try:
        document = update.message.document
        
        if document.mime_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            update.message.reply_text("❌ يرجى إرسال ملف PPTX فقط")
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            # تنزيل الملف
            file = context.bot.get_file(document.file_id)
            input_path = os.path.join(tmp_dir, document.file_name)
            file.download(input_path)
            
            # الترجمة
            output_path = os.path.join(tmp_dir, "translated.pptx")
            translated_path = translate_pptx(input_path, output_path)
            
            # إرسال النتيجة
            with open(translated_path, 'rb') as f:
                update.message.reply_document(
                    document=f,
                    caption="تمت الترجمة بنجاح ✅",
                    filename=os.path.basename(translated_path)
                )
                
    except Exception as e:
        error_msg = f"فشلت العملية: {str(e)}"
        update.message.reply_text(error_msg)
        print(f"Error Trace: {str(e)}")

def main():
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
