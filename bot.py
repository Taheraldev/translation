import os
import logging
import openai
import PyPDF2
from fpdf import FPDF
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# الحصول على القيم من متغيرات البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# التحقق من وجود المفاتيح
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("يرجى ضبط متغيرات البيئة TELEGRAM_TOKEN و OPENAI_API_KEY في ملف .env")

openai.api_key = OPENAI_API_KEY  # ضبط API Key لـ OpenAI

# إعداد تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    await update.message.reply_text("👋 مرحبًا! أرسل لي ملف PDF وسأقوم بترجمته من الإنجليزية إلى العربية.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع ملفات PDF"""
    document = update.message.document
    if document.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ يرجى إرسال ملف PDF صحيح.")
        return

    # تنزيل ملف PDF
    file = await document.get_file()
    input_filename = "input.pdf"
    await file.download_to_drive(input_filename)

    # استخراج النص من ملف PDF
    extracted_text = ""
    try:
        with open(input_filename, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        logging.error("❌ خطأ أثناء استخراج النص: %s", e)
        await update.message.reply_text("❌ حدث خطأ أثناء قراءة الملف.")
        return

    if not extracted_text.strip():
        await update.message.reply_text("⚠️ لم يتمكن من استخراج أي نص من الملف.")
        return

    # ترجمة النص باستخدام OpenAI
    prompt = f"ترجم النص التالي من الإنجليزية إلى العربية مع الحفاظ على المعنى:\n\n{extracted_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        translated_text = response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("❌ خطأ أثناء الترجمة: %s", e)
        await update.message.reply_text("❌ حدث خطأ أثناء الترجمة.")
        return

    # إنشاء ملف PDF جديد بالنص المترجم
    output_filename = "translated.pdf"
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        for line in translated_text.split('\n'):
            pdf.multi_cell(0, 10, line)
        
        pdf.output(output_filename)
    except Exception as e:
        logging.error("❌ خطأ أثناء إنشاء ملف PDF: %s", e)
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الملف المترجم.")
        return

    # إرسال الملف المترجم إلى المستخدم
    try:
        with open(output_filename, "rb") as translated_file:
            await update.message.reply_document(document=translated_file)
    except Exception as e:
        logging.error("❌ خطأ أثناء إرسال الملف: %s", e)
        await update.message.reply_text("❌ حدث خطأ أثناء إرسال الملف.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء العامة"""
    logging.error("⚠️ حدث خطأ: %s", context.error)

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.add_error_handler(error_handler)

    # تشغيل البوت في وضع الاستماع المستمر
    application.run_polling()

if __name__ == "__main__":
    main()
