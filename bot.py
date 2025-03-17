import os
import requests
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.pdf_file_request import PdfFileRequest
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# بيانات GroupDocs
CLIENT_ID = "a91a6ad1-7637-4e65-b793-41af55450807"
CLIENT_SECRET = "2d0c949f2cc2d12010f5427e6c1dc4da"

# تهيئة GroupDocs API
configuration = groupdocs_translation_cloud.Configuration(CLIENT_ID, CLIENT_SECRET)
translation_api = groupdocs_translation_cloud.TranslationApi(groupdocs_translation_cloud.ApiClient(configuration))

# دالة لترجمة ملف PDF
def translate_pdf(file_path):
    try:
        # تحضير طلب الترجمة
        pdf_file_request = PdfFileRequest(
            name="document.pdf",
            source_language="en",
            target_language="ar",
            file=file_path
        )

        # إرسال طلب الترجمة
        response = translation_api.pdf_post(pdf_file_request=pdf_file_request)
        return response.url  # رابط تنزيل الملف المترجم
    except Exception as e:
        print("حدث خطأ أثناء الترجمة:", e)
        return None

# دالة لمعالجة الأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل لي ملف PDF وسأقوم بترجمته من الإنجليزية إلى العربية.")

# دالة لمعالجة الملفات المرسلة
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تنزيل الملف المرسل
    file = await update.message.document.get_file()
    file_path = f"temp_{update.message.document.file_name}"
    await file.download_to_drive(file_path)

    # ترجمة الملف
    download_url = translate_pdf(file_path)
    if download_url:
        # تنزيل الملف المترجم
        translated_file_path = f"translated_{update.message.document.file_name}"
        response = requests.get(download_url)
        with open(translated_file_path, "wb") as f:
            f.write(response.content)

        # إرسال الملف المترجم للمستخدم
        await update.message.reply_document(document=InputFile(translated_file_path))
        os.remove(translated_file_path)  # حذف الملف بعد الإرسال
    else:
        await update.message.reply_text("حدث خطأ أثناء ترجمة الملف. يرجى المحاولة مرة أخرى.")

    # حذف الملف المؤقت
    os.remove(file_path)

# الدالة الرئيسية
def main():
    # Token البوت (استبدله بـ Token الخاص بك)
    TELEGRAM_TOKEN = "5146976580:AAHc3N58Bbxh1-D2ydnA-BNlLmhXJ5kl1c0"

    # تهيئة البوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()
