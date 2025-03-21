import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from googletrans import Translator

# إعدادات البوت
TOKEN = os.getenv("TOKEN")
translator = Translator()

# الخط المستخدم للكتابة على الصورة (يجب توفير ملف الخط يدويًا)
FONT_PATH = "arial.ttf"  # استبدل بمسار ملف الخط العربي (مثال: tajawal.ttf)

# تفعيل اللوغاريثمات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('مرحبًا! أرسل لي صورة تحتوي على نص إنجليزي وسأترجمها إلى العربية مع استبدال النص في الصورة.')

def handle_photo(update: Update, context: CallbackContext):
    try:
        # تحميل الصورة
        photo_file = update.message.photo[-1].get_file()
        photo_path = 'temp_image.jpg'
        photo_file.download(photo_path)
        
        # معالجة الصورة
        img = Image.open(photo_path)
        
        # استخراج النص الإنجليزي ومواقعه
        data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)
        
        # ترجمة النصوص المكتشفة
        translated_texts = [translator.translate(text, src='en', dest='ar').text for text in data['text']]
        
        # رسم النص المترجم على الصورة
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT_PATH, 20)  # اضبط حجم الخط حسب الحاجة
        
        for i in range(len(data['text'])):
            if data['text'][i].strip() != '':
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # رسم خلفية بيضاء مكان النص الأصلي
                draw.rectangle([x, y, x + w, y + h], fill="white")
                
                # كتابة النص المترجم (باستخدام الخط العربي)
                draw.text((x, y), translated_texts[i], font=font, fill="black")
        
        # حفظ الصورة المعدلة
        output_path = "translated_image.jpg"
        img.save(output_path)
        
        # إرسال الصورة المترجمة
        update.message.reply_photo(photo=open(output_path, "rb"))
        
        # حذف الملفات المؤقتة
        os.remove(photo_path)
        os.remove(output_path)
        
    except Exception as e:
        update.message.reply_text(f"حدث خطأ: {str(e)}")

def main():
    # إنشاء Updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # إضافة handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_photo))
    
    # تشغيل البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
