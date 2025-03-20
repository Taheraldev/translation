import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ضع هنا مفاتيحك الخاصة
TELEGRAM_BOT_TOKEN = "5284087690:AAGwKfPojQ3c-SjCHSIdeog-yN3-4Gpim1Y"  # احصل عليه من BotFather
PIXVERSE_API_URL = "https://pixverse.ai/api/generate"  # تأكد من صحة عنوان API حسب التوثيق
PIXVERSE_API_KEY = "sk-25930e94a9e040d0cf639d1da94a2c76"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل وصفاً للصورة التي تريد إنشاؤها عبر pixverse.ai.")

def generate_image(update: Update, context: CallbackContext):
    description = update.message.text
    headers = {
        "Authorization": f"Bearer {PIXVERSE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "description": description
        # يمكنك إضافة خيارات إضافية حسب متطلبات API (مثل حجم الصورة أو نوع التوليد)
    }
    
    try:
        response = requests.post(PIXVERSE_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            image_url = data.get("image_url")  # تأكد من المفتاح الصحيح بحسب استجابة API
            if image_url:
                update.message.reply_photo(photo=image_url)
            else:
                update.message.reply_text("لم يتم استلام رابط الصورة من API.")
        else:
            update.message.reply_text(f"حدث خطأ أثناء معالجة الطلب (الكود: {response.status_code}).")
    except Exception as e:
        update.message.reply_text("حدث خطأ أثناء الاتصال بـ API.")
        print(e)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, generate_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
