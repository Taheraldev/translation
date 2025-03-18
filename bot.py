import os
import fitz  # PyMuPDF
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pyreverso import Reverso
from fpdf import FPDF

# إعداد سجل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# استبدل هذا بالتوكن الخاص بك من بوت فاذر
TELEGRAM_BOT_TOKEN = "6016945663:AAHjacRdRfZ2vUgS2SLmoFgHfMdUye4l6bA"

# استخراج النص من PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

# ترجمة النص باستخدام Reverso
def translate_text(text, source_lang="en", target_lang="ar"):
    reverso = Reverso(text, source_lang, target_lang)
    translations = reverso.get_translation()
    return " ".join(translations)

# إنشاء PDF جديد مع النص المترجم
def create_translated_pdf(translated_text, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, translated_text)
    pdf.output(output_path)

# التعامل مع استلام الملفات
async def handle_document(update: Update, context: CallbackContext) -> None:
    file = await update.message.document.get_file()
    file_path = f"downloads/{file.file_id}.pdf"
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)
    
    update.message.reply_text("جارٍ استخراج النص من الملف...")
    extracted_text = extract_text_from_pdf(file_path)
    
    update.message.reply_text("جارٍ الترجمة، يرجى الانتظار...")
    translated_text = translate_text(extracted_text)
    
    output_path = file_path.replace(".pdf", "_translated.pdf")
    create_translated_pdf(translated_text, output_path)
    
    with open(output_path, "rb") as pdf_file:
        await update.message.reply_document(document=pdf_file, filename="translated.pdf")
    
    os.remove(file_path)
    os.remove(output_path)

# بدء البوت
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("مرحبًا! أرسل لي ملف PDF وسأقوم بترجمته لك من الإنجليزية إلى العربية.")

if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))
    
    print("🤖 البوت يعمل... انتظر الرسائل!")
    app.run_polling()
