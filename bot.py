import logging
import os
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import PyPDF2
from fpdf import FPDF

# إعداد التوكن الخاص بتليجرام ومفتاح OpenAI
openai.api_key = OPENAI_API_KEY

# تفعيل تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل لي ملف PDF للترجمة من الإنجليزية إلى العربية.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document.mime_type != 'application/pdf':
        await update.message.reply_text("يرجى إرسال ملف PDF صحيح.")
        return

    # تنزيل ملف PDF
    file = await document.get_file()
    input_filename = "input.pdf"
    await file.download_to_drive(input_filename)
    
    # استخراج النص من ملف PDF باستخدام PyPDF2
    extracted_text = ""
    try:
        with open(input_filename, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    except Exception as e:
        logging.error("Error reading PDF: %s", e)
        await update.message.reply_text("حدث خطأ أثناء قراءة الملف.")
        return

    # التحقق من وجود نص لاستخراجه
    if not extracted_text.strip():
        await update.message.reply_text("لم يتمكن من استخراج أي نص من الملف.")
        return

    # ترجمة النص باستخدام OpenAI
    prompt = f"ترجم النص التالي من اللغة الإنجليزية إلى العربية مع الحفاظ على التنسيق قدر الإمكان:\n\n{extracted_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        translated_text = response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("Error during translation: %s", e)
        await update.message.reply_text("حدث خطأ أثناء الترجمة.")
        return

    # إنشاء ملف PDF جديد بالنص المترجم باستخدام FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    
    # تقسيم النص إلى أسطر وإضافتها للملف
    for line in translated_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    output_filename = "translated.pdf"
    try:
        pdf.output(output_filename)
    except Exception as e:
        logging.error("Error generating PDF: %s", e)
        await update.message.reply_text("حدث خطأ أثناء إنشاء الملف المترجم.")
        return

    # إرسال ملف PDF المترجم للمستخدم
    try:
        with open(output_filename, "rb") as translated_file:
            await update.message.reply_document(document=translated_file)
    except Exception as e:
        logging.error("Error sending PDF: %s", e)
        await update.message.reply_text("حدث خطأ أثناء إرسال الملف.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.add_error_handler(error_handler)

    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
