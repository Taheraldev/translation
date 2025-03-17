import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد اللوجينج لتتبع الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد متغيرات API الترجمة
APYHUB_TOKEN = "APY0HI85jCUZwP9yaXqm9Yb4tEDRJ5uv2ht8jpP7PsVo8sGeWkmDAmHYM2V4Q8U7Z13gmqjzE"
TRANSLATE_FILE_URL = "https://api.apyhub.com/translate/file"

# الصيغ المدعومة
ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'html', 'xml']

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("مرحباً! أرسل لي ملفاً (مثل pdf أو docx) وسأقوم بترجمته من الإنجليزية إلى العربية.")

def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    file_name = document.file_name
    ext = file_name.split('.')[-1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        update.message.reply_text("صيغة الملف غير مدعومة.")
        return
    
    # تحميل الملف من تيليجرام وحفظه محليًا
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)
    new_file = context.bot.getFile(document.file_id)
    new_file.download(file_path)
    
    update.message.reply_text("تم استلام الملف، جارٍ الترجمة...")

    try:
        # إعداد الرؤوس والباراميترات للطلب
        headers = {
            'apy-token': APYHUB_TOKEN
        }
        params = {
            'transliteration': 'true'
        }
        files_payload = {
            'file': open(file_path, 'rb'),
            'language': (None, 'ar')  # نحدد هنا اللغة المطلوبة (العربية)
        }
        
        # إرسال الطلب إلى API الترجمة
        response = requests.post(TRANSLATE_FILE_URL, params=params, headers=headers, files=files_payload)
        
        if response.status_code == 200:
            data = response.json()
            detected = data.get("detected_language", {})
            detected_lang = detected.get("language", "غير معروف")
            detected_score = detected.get("score", 0)
            translated_language = data.get("translated_language", "غير معروف")
            translation_text = data.get("translation", "")
            transliteration_text = data.get("transliteration", "")
            
            # إعداد رسالة الرد
            reply_message = f"تم الكشف عن اللغة: {detected_lang} (نسبة: {detected_score})\n"
            reply_message += f"تم الترجمة إلى: {translated_language}\n\n"
            reply_message += f"الترجمة:\n{translation_text}\n\n"
            reply_message += f"النطق بالحروف اللاتينية:\n{transliteration_text}"
            
            update.message.reply_text(reply_message)
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            update.message.reply_text("حدث خطأ أثناء الترجمة. الرجاء المحاولة لاحقاً.")
    except Exception as e:
        logger.exception("Exception occurred during translation:")
        update.message.reply_text("حدث خطأ أثناء معالجة الملف.")
    finally:
        # حذف الملف المحلي بعد المعالجة
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    TELEGRAM_TOKEN = "5136337543:AAHG1tqXdpVaB-zWUn8pREf9tBi211sv6Ys"  # استبدل هذا بتوكن البوت الخاص بك
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
