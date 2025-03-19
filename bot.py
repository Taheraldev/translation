import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import io
from PyPDF2 import PdfReader
from docx import Document

# استبدل هذه القيم برموز API الخاصة بك
TELEGRAM_BOT_TOKEN = "5284087690:AAGwKfPojQ3c-SjCHSIdeog-yN3-4Gpim1Y"
SMARTCAT_API_KEY = "2_FwEmd5QMpKxDbHnNnwydzEL3o"

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="أرسل لي ملف PDF لترجمته.")

def translate_pdf(update, context):
    try:
        # تنزيل ملف PDF
        file_id = update.message.document.file_id
        file_info = context.bot.get_file(file_id)
        file = requests.get(file_info.file_path)
        pdf_file = io.BytesIO(file.content)

        # استخراج النص من ملف PDF
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # ترجمة النص باستخدام Smartcat API
        headers = {
            "Authorization": f"Bearer {SMARTCAT_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "sourceLanguage": "en",
            "targetLanguages": ["ar"],
            "content": text,
        }
        response = requests.post(
            "https://api.smartcat.com/v1/translate", headers=headers, json=data
        )
        translated_text = response.json()["translations"]["ar"]

        # إنشاء ملف DOCX من النص المترجم
        document = Document()
        document.add_paragraph(translated_text)
        docx_file = io.BytesIO()
        document.save(docx_file)
        docx_file.seek(0)

        # إرسال ملف DOCX إلى المستخدم
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=docx_file,
            filename="translated.docx",
        )

    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"حدث خطأ أثناء الترجمة: {str(e)}",
        )

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher # تم تغيير الاسم إلى dp
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), translate_pdf))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
