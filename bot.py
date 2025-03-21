import logging
import os
import convertapi
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد ConvertAPI
CONVERTAPI_SECRET = "secret_ZJOY2tBFX1c3T3hA"
convertapi.api_secret = CONVERTAPI_SECRET

# إعدادات البوت
TOKEN = "5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc"
DOWNLOAD_PATH = "downloads"
OUTPUT_PATH = "output"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

# تهيئة اللوجينج
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("أرسل ملف PDF لتحويله إلى DOCX.")

def convert_pdf_to_docx(pdf_path: str) -> str:
    try:
        logging.info(f"Converting file: {pdf_path}")
        result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf')
        
        if not result:
            logging.error("ConvertAPI returned None")
            return None
        
        if not hasattr(result, "save_files"):
            logging.error("Result object has no 'save_files' method")
            return None
        
        docx_files = result.save_files(OUTPUT_PATH)
        
        if not docx_files:
            logging.error("No files were saved by ConvertAPI")
            return None
        
        return docx_files[0]
    except Exception as e:
        logging.error(f"Error during conversion: {e}")
        return None

def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if file.mime_type != "application/pdf":
        update.message.reply_text("يرجى إرسال ملف PDF فقط.")
        return
    
    pdf_file = file.get_file()
    file_path = os.path.join(DOWNLOAD_PATH, file.file_name)
    pdf_file.download(file_path)
    
    update.message.reply_text("جارٍ تحويل الملف، يرجى الانتظار...")
    
    docx_path = convert_pdf_to_docx(file_path)
    
    if docx_path:
        update.message.reply_document(document=open(docx_path, "rb"), filename=os.path.basename(docx_path))
    else:
        update.message.reply_text("حدث خطأ أثناء التحويل. الرجاء المحاولة لاحقًا.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
