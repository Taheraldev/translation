import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image
import pytesseract
from googletrans import Translator

# إعدادات البوت
TOKEN = os.getenv("TOKEN")  # الحصول على التوكن من متغيرات البيئة
translator = Translator()

# تفعيل اللوغاريثمات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('مرحبًا! أرسل لي صورة تحتوي على نص إنجليزي وسأترجمه للعربية.')

def handle_photo(update: Update, context: CallbackContext):
    # تحميل الصورة
    photo_file = update.message.photo[-1].get_file()
    photo_path = 'temp_image.jpg'
    photo_file.download(photo_path)
    
    # معالجة الصورة باستخدام OCR
    img = Image.open(photo_path)
    english_text = pytesseract.image_to_string(img, lang='eng')
    
    # الترجمة إلى العربية
    translation = translator.translate(english_text, src='en', dest='ar')
    
    # إرسال النتيجة
    update.message.reply_text(f'الترجمة:\n{translation.text}')
    
    # حذف الصورة المؤقتة
    os.remove(photo_path)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_photo))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
