import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد اللوجينج لتتبع الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# بيانات API الترجمة
TRANSLATION_API_KEY = "APY0Urd1nyxwRe0hwBMa9bk0s2ttKyrSBv5scX9rsv9A2ZkzvATiUoblyVM1JwD0Y"
TRANSLATION_API_URL = "https://api.example.com/translate"  # استبدل هذا بعنوان نقطة النهاية الفعلي للـ API

# دالة بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "مرحباً! أرسل لي ملفاً (مثل pdf أو docx) وسأقوم بترجمته من الإنجليزية إلى العربية."
    )

# دالة التعامل مع الملفات المرسلة
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    file_name = document.file_name
    # التأكد من أن صيغة الملف مدعومة
    allowed_extensions = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'html', 'xml']
    ext = file_name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        await update.message.reply_text("صيغة الملف غير مدعومة.")
        return

    # تحميل الملف من تيليجرام
    file = await context.bot.get_file(document.file_id)
    local_file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(local_file_path)
    await update.message.reply_text("تم استلام الملف، جاري الترجمة...")

    try:
        # إعداد الطلب للـ API
        payload = {
            "source_lang": "en",  # اللغة الأصلية
            "target_lang": "ar"   # اللغة المستهدفة
        }
        headers = {
            "Authorization": f"Bearer {TRANSLATION_API_KEY}"
        }
        with open(local_file_path, "rb") as f:
            files = {
                "file": (file_name, f)
            }
            response = requests.post(TRANSLATION_API_URL, data=payload, files=files, headers=headers)
        
        if response.status_code == 200:
            # حفظ الملف المترجم
            translated_file_path = f"downloads/translated_{file_name}"
            with open(translated_file_path, "wb") as out_file:
                out_file.write(response.content)
            await update.message.reply_text("تمت الترجمة بنجاح، جارٍ إرسال الملف...")
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(translated_file_path, "rb"))
            os.remove(translated_file_path)
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            await update.message.reply_text("حدث خطأ أثناء الترجمة.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("حدث خطأ أثناء معالجة الملف.")
    finally:
        os.remove(local_file_path)

def main() -> None:
    # ضع هنا توكن البوت الخاص بك من تيليجرام
    TELEGRAM_TOKEN = "5136337543:AAHG1tqXdpVaB-zWUn8pREf9tBi211sv6Ys"  # استبدله بتوكن البوت الخاص بك

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # تسجيل المعالجات (handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # تشغيل البوت باستخدام polling
    application.run_polling()

if __name__ == "__main__":
    main()
