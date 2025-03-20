import os
import requests
import tempfile
import pdfplumber
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعدادات API للترجمة
API_URL = "https://openl-translate.p.rapidapi.com/translate/bulk"
HEADERS = {
    "X-RapidAPI-Key": "7b73717e2dmshbd139747c640560p175307jsn75624bf31396",
    "X-RapidAPI-Host": "openl-translate.p.rapidapi.com",
    "Content-Type": "application/json"
}

# دالة الترجمة عبر OpenL API
def translate_text(text: str, source_lang="en", target_lang="ar") -> str:
    response = requests.post(API_URL, json={"text": [text], "source_lang": source_lang, "target_lang": target_lang}, headers=HEADERS)
    if response.status_code == 200:
        translated_text = response.json().get("translations", [{}])[0].get("text", "")
        return translated_text
    return text  # في حال فشل الترجمة، يرجع النص الأصلي

# دالة معالجة PDF
def translate_pdf(file_path):
    new_pdf_path = file_path.replace(".pdf", "_translated.pdf")
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        translated_text = translate_text(text)
        page.insert_text((50, 50), translated_text, fontsize=12)
    doc.save(new_pdf_path)
    return new_pdf_path

# دالة معالجة DOCX
def translate_docx(file_path):
    new_docx_path = file_path.replace(".docx", "_translated.docx")
    doc = Document(file_path)
    for para in doc.paragraphs:
        para.text = translate_text(para.text)
    doc.save(new_docx_path)
    return new_docx_path

# دالة معالجة PPTX
def translate_pptx(file_path):
    new_pptx_path = file_path.replace(".pptx", "_translated.pptx")
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                shape.text = translate_text(shape.text)
    prs.save(new_pptx_path)
    return new_pptx_path

# دالة استقبال الملفات من تيليجرام
def handle_document(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    ext = file.file_path.split(".")[-1].lower()
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, f"file.{ext}")
    file.download(temp_file)
    
    if ext == "pdf":
        translated_file = translate_pdf(temp_file)
    elif ext == "docx":
        translated_file = translate_docx(temp_file)
    elif ext == "pptx":
        translated_file = translate_pptx(temp_file)
    else:
        update.message.reply_text("❌ الملف غير مدعوم! الرجاء إرسال PDF أو DOCX أو PPTX.")
        return
    
    with open(translated_file, "rb") as f:
        update.message.reply_document(InputFile(f, filename=os.path.basename(translated_file)), caption="✅ تم الترجمة بنجاح!")



# تهيئة البوت
def main():
    updater = Updater("5284087690:AAGwKfPojQ3c-SjCHSIdeog-yN3-4Gpim1Y", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
