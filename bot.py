import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
# استيراد مكتبة GroupDocs Translation Cloud
from groupdocs_translation_cloud import Configuration, TranslateApi, TranslateDocumentRequest

# إعداد بيانات اعتماد GroupDocs
CLIENT_ID = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
CLIENT_SECRET = "20c8c4f0947d9901282ee3576ec31535"

config = Configuration(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
translation_api = TranslateApi(config)

# إعداد رمز البوت الخاص بتليجرام
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # ضع هنا رمز البوت الخاص بك

# إعداد مسار حفظ الملفات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تعليمات للمستخدم عند بدء المحادثة"""
    await update.message.reply_text("مرحباً! أرسل لي ملف PowerPoint (pptx) للترجمة من الإنجليزية إلى العربية.")

def translate_file(file_path: str) -> str:
    """
    دالة لترجمة الملف باستخدام GroupDocs Translation Cloud.
    تأخذ مسار الملف المرسل وتعيد مسار الملف المترجم.
    """
    request = TranslateDocumentRequest(
        file_path=file_path,     # مسار الملف المحلي
        target_language="ar",    # اللغة الهدف: العربية
        source_language="en"     # اللغة المصدر: الإنجليزية
    )
    
    # تنفيذ طلب الترجمة
    result = translation_api.translate_document(request)
    
    # حفظ الملف المترجم
    translated_file_path = os.path.join(DOWNLOAD_DIR, "translated_" + os.path.basename(file_path))
    with open(translated_file_path, "wb") as f:
        f.write(result)
    
    return translated_file_path

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الملف المرسل من المستخدم"""
    if update.message.document is None:
        return
    
    document = update.message.document
    file_name = document.file_name
    
    if not file_name.lower().endswith(".pptx"):
        await update.message.reply_text("الملف المرسل ليس بتنسيق pptx.")
        return

    # تحميل الملف من تليجرام
    file = await context.bot.get_file(document.file_id)
    local_file_path = os.path.join(DOWNLOAD_DIR, file_name)
    await file.download_to_drive(custom_path=local_file_path)
    
    await update.message.reply_text("جاري ترجمة الملف، يرجى الانتظار...")
    
    try:
        translated_file_path = translate_file(local_file_path)
        # إرسال الملف المترجم للمستخدم
        with open(translated_file_path, "rb") as translated_file:
            await update.message.reply_document(document=translated_file)
        await update.message.reply_text("تمت الترجمة بنجاح!")
    except Exception as e:
        logger.error("خطأ أثناء الترجمة: %s", e)
        await update.message.reply_text("حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.")

async def main() -> None:
    """بدء تشغيل البوت باستخدام ApplicationBuilder"""
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PRESENT, handle_document))

    # بدء البوت بطريقة غير متزامنة
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
