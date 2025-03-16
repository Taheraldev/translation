import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# استيراد مكتبة GroupDocs Translation Cloud
from groupdocs_translation_cloud import Configuration, TranslationApi
from groupdocs_translation_cloud.models import TranslateOptions, TranslateDocumentRequest

# إعداد السجل (Logging)
logging.basicConfig(level=logging.INFO)

# بيانات اعتماد GroupDocs Translation Cloud
CLIENT_ID = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
CLIENT_SECRET = "20c8c4f0947d9901282ee3576ec31535"

# تهيئة إعدادات المكتبة وإنشاء العميل الخاص بالترجمة
config = Configuration(CLIENT_ID, CLIENT_SECRET)
translation_api = TranslationApi(config)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("أهلاً! أرسل ملف PPTX للترجمة من الإنجليزية إلى العربية.")

def document_handler(update: Update, context: CallbackContext):
    document = update.message.document
    # التأكد من أن الملف من نوع PPTX
    if document.file_name.lower().endswith(".pptx"):
        # إنشاء مجلد لتحميل الملفات إذا لم يكن موجوداً
        os.makedirs("downloads", exist_ok=True)
        input_path = os.path.join("downloads", document.file_name)
        
        # تحميل الملف من تليجرام
        file = context.bot.get_file(document.file_id)
        file.download(custom_path=input_path)
        update.message.reply_text("تم تحميل الملف، جارٍ الترجمة...")
        
        # تحديد مسار الملف المترجم
        output_file_name = "translated_" + document.file_name
        output_path = os.path.join("downloads", output_file_name)
        
        try:
            # إعداد خيارات الترجمة
            translate_options = TranslateOptions(
                file_path=input_path,   # مسار الملف الأصلي
                output_path=output_path,  # مسار الملف الناتج
                source_language="en",     # اللغة الأصلية (إنجليزية)
                target_language="ar"      # اللغة الهدف (عربية)
            )
            # إنشاء الطلب الخاص بالترجمة
            request = TranslateDocumentRequest(translate_options)
            # تنفيذ عملية الترجمة عبر API
            response = translation_api.translate_document(request)
            
            # إرسال الملف المترجم للمستخدم
            with open(output_path, "rb") as f:
                update.message.reply_document(document=f)
            update.message.reply_text("تمت الترجمة بنجاح!")
            
            # حذف الملفات المؤقتة (اختياري)
            os.remove(input_path)
            os.remove(output_path)
        except Exception as e:
            logging.error("خطأ أثناء الترجمة: %s", e)
            update.message.reply_text(f"حدث خطأ أثناء الترجمة: {e}")
    else:
        update.message.reply_text("الرجاء إرسال ملف من نوع PPTX فقط.")

def main():
    # أدخل توكن بوت التليجرام الخاص بك هنا
    TELEGRAM_BOT_TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"
    
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # أوامر البوت
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, document_handler))
    
    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
