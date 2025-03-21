import os
import convertapi
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# إعداد مفتاح ConvertAPI
CONVERT_API_KEY = "secret_ZJOY2tBFX1c3T3hA"
convertapi.api_secret = CONVERT_API_KEY

# مجلد التخزين المؤقت
TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("أرسل ملف PDF أو DOCX أو PPTX لتحويله.")

def show_conversion_options(update: Update, context: CallbackContext, file_id: str, file_name: str):
    context.user_data['file_id'] = file_id
    context.user_data['file_name'] = file_name
    keyboard = [
        [InlineKeyboardButton("تحويل إلى DOCX", callback_data="pdf2docx")],
        [InlineKeyboardButton("تحويل إلى PPTX", callback_data="pdf2pptx")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر نوع التحويل:", reply_markup=reply_markup)

def convert_file(input_path: str, output_format: str, output_path: str):
    convertapi.convert(output_format, {'File': input_path}).save_files(output_path)

def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    file_id = file.file_id
    file_name = file.file_name.lower()
    
    if file.mime_type == "application/pdf":
        show_conversion_options(update, context, file_id, file_name)
    elif file.mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
        context.user_data['file_id'] = file_id
        context.user_data['file_name'] = file_name
        keyboard = [[InlineKeyboardButton("تحويل إلى PDF", callback_data="to_pdf")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر نوع التحويل:", reply_markup=reply_markup)
    else:
        update.message.reply_text("صيغة الملف غير مدعومة.")

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    action = query.data
    file_id = context.user_data.get('file_id')
    file_name = context.user_data.get('file_name')
    
    if not file_id or not file_name:
        query.edit_message_text("حدث خطأ، يرجى إعادة إرسال الملف.")
        return
    
    file_path = os.path.join(TEMP_FOLDER, file_name)
    output_format = "pdf" if action == "to_pdf" else action.replace("pdf2", "")
    output_path = file_path.rsplit(".", 1)[0] + f".{output_format}"
    
    pdf_file = context.bot.getFile(file_id)
    pdf_file.download(file_path)
    
    query.edit_message_text("جارٍ تحويل الملف... يرجى الانتظار.")
    try:
        convert_file(file_path, output_format, output_path)
        query.message.reply_document(document=open(output_path, "rb"))
    except Exception as e:
        query.message.reply_text(f"حدث خطأ أثناء التحويل: {str(e)}")
    finally:
        os.remove(file_path)
        os.remove(output_path)

def main():
    updater = Updater("5264968049:AAHUniq68Nqq39CrFf8lVqerwetirQnGxzc", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
