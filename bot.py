import os
import logging
import pdfplumber
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from deep_translator import GoogleTranslator

# إعدادات اللوج
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# حد أقصى لحجم الملف 1MB
MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# عدد الملفات المسموح بها يوميًا لكل مستخدم
MAX_FILES_PER_DAY = 5

# حد أقصى لعدد الصفحات
MAX_PAGES = 5

# تخزين عدد الملفات المرسلة لكل مستخدم
user_file_counts = {}

# استخراج النص من PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) > MAX_PAGES:
            return None, "❌ الملف يحتوي على أكثر من 5 صفحات!"
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text, None

# ترجمة النص باستخدام Google Translate
def translate_text(text, src_lang="auto", dest_lang="ar"):
    translator = GoogleTranslator(source=src_lang, target=dest_lang)
    return translator.translate(text)

# إنشاء ملف HTML
def save_translated_html(text, output_path):
    html_content = f"<html><body><p>{text.replace('\n', '<br>')}</p></body></html>"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

# بدء التعامل مع ملفات PDF
def handle_pdf(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    file = update.message.document

    # التأكد من أن الملف بصيغة PDF فقط
    if not file.mime_type == "application/pdf":
        update.message.reply_text("❌ يُسمح فقط بملفات PDF!")
        return

    # التحقق من الحد اليومي للملفات
    user_file_counts[user_id] = user_file_counts.get(user_id, 0) + 1
    if user_file_counts[user_id] > MAX_FILES_PER_DAY:
        update.message.reply_text("❌ لقد تجاوزت الحد اليومي لعدد الملفات (5 ملفات)!")
        return

    # التحقق من حجم الملف
    if file.file_size > MAX_FILE_SIZE_BYTES:
        update.message.reply_text(f"❌ الحد الأقصى لحجم الملف هو {MAX_FILE_SIZE_MB}MB!")
        return

    # تنزيل الملف
    pdf_path = f"downloads/{file.file_id}.pdf"
    os.makedirs("downloads", exist_ok=True)
    file.get_file().download(pdf_path)

    # استخراج النص
    extracted_text, error = extract_text_from_pdf(pdf_path)
    if error:
        update.message.reply_text(error)
        return

    if not extracted_text.strip():
        update.message.reply_text("❌ لم يتم العثور على نص في الملف!")
        return

    # ترجمة النص
    translated_text = translate_text(extracted_text)

    # إنشاء ملف HTML
    html_path = pdf_path.replace(".pdf", ".html")
    save_translated_html(translated_text, html_path)

    # إرسال الملف المترجم
    with open(html_path, "rb") as html_file:
        update.message.reply_document(document=html_file, filename="translated.html", caption="✅ تم ترجمة الملف بنجاح!")

# دالة البدء
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 أهلاً بك! أرسل لي ملف PDF وسأقوم بترجمته لك.")

def main():
    TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
