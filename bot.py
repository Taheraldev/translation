import logging
import io
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pdfcrowd

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات PDFCrowd
PDFCROWD_USERNAME = "taherja"
PDFCROWD_API_KEY = "4f59bd9b2030deabe9d14c92ed65817a"

# ضع توكن بوت تليجرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحباً! أرسل لي ملف HTML لأقوم بتحويله إلى PDF.')

def convert_html_to_pdf(html_content: str) -> bytes:
    """
    تحويل نص HTML إلى PDF باستخدام PDFCrowd API.
    """
    try:
        client = pdfcrowd.HtmlToPdfClient(PDFCROWD_USERNAME, PDFCROWD_API_KEY)
        # استخدام BytesIO لتخزين الملف في الذاكرة
        output_stream = io.BytesIO()
        client.convertStringToStream(html_content, output_stream)
        output_stream.seek(0)
        return output_stream.read()
    except pdfcrowd.Error as e:
        logger.error("PDFCrowd Error: %s", e)
        return None

def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    # التأكد من أن الملف هو HTML
    if document.mime_type != 'text/html' and not document.file_name.endswith('.html'):
        update.message.reply_text('يرجى إرسال ملف HTML فقط.')
        return

    # تنزيل الملف باستخدام الطريقة المتوافقة مع python-telegram-bot==13.15
    file_obj = context.bot.get_file(document.file_id)
    bio = io.BytesIO()
    file_obj.download(out=bio)
    bio.seek(0)

    try:
        html_content = bio.read().decode('utf-8')
    except UnicodeDecodeError:
        update.message.reply_text('تعذر قراءة الملف، يرجى التأكد من ترميز UTF-8.')
        return

    # تحويل HTML إلى PDF
    pdf_bytes = convert_html_to_pdf(html_content)
    if pdf_bytes is None:
        update.message.reply_text('حدث خطأ أثناء عملية التحويل.')
        return

    # إرسال ملف PDF للمستخدم
    pdf_file = io.BytesIO(pdf_bytes)
    pdf_file.name = 'converted.pdf'
    update.message.reply_document(document=pdf_file, filename='converted.pdf')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
