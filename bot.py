import os
import convertapi
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد مفتاح ConvertAPI
CONVERT_API_KEY = "secret_ZJOY2tBFX1c3T3hA"
convertapi.api_secret = CONVERT_API_KEY

# مجلد التخزين المؤقت
TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("أرسل ملف PDF لتحويله إلى DOCX.")

def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    convertapi.convert('docx', {'File': pdf_path}, from_format='pdf').save_files(docx_path)

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    if file.mime_type != "application/pdf":
        update.message.reply_text("يرجى إرسال ملف PDF فقط.")
        return
    
    file_path = os.path.join(TEMP_FOLDER, file.file_name)
    docx_path = file_path.replace(".pdf", ".docx")
    
    pdf_file = context.bot.getFile(file.file_id)
    pdf_file.download(file_path)
    
    update.message.reply_text("جارٍ تحويل الملف... يرجى الانتظار.")
    try:
        convert_pdf_to_docx(file_path, docx_path)
        update.message.reply_document(document=open(docx_path, "rb"))
    except Exception as e:
        update.message.reply_text(f"حدث خطأ أثناء التحويل: {str(e)}")
    finally:
        os.remove(file_path)
        os.remove(docx_path)

def main():
    updater = Updater("5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
