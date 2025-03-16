import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from pptx import Presentation
from deepseek_api import translate_text  # استبدل هذا بالواجهة الفعلية

# إعدادات البوت
TOKEN = "5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A"
API_KEY = "sk-6f67b496dded4e8784dbee59f08d8d7f"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    if document.mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        file = await context.bot.get_file(document.file_id)
        original_path = f"temp_{document.file_id}.pptx"
        translated_path = f"translated_{document.file_id}.pptx"
        
        await file.download_to_drive(original_path)
        
        # عملية الترجمة
        prs = Presentation(original_path)
        translate_presentation(prs)
        prs.save(translated_path)
        
        await update.message.reply_document(document=open(translated_path, 'rb'))
        
        # تنظيف الملفات المؤقتة
        os.remove(original_path)
        os.remove(translated_path)
    else:
        await update.message.reply_text("الرجاء إرسال ملف بوربوينت بصيغة PPTX")

def translate_presentation(presentation):
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                if shape.text.strip():
                    translated = translate_text(shape.text, "en", "ar", API_KEY)
                    shape.text = translated
                    
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            translated = translate_text(cell.text, "en", "ar", API_KEY)
                            cell.text = translated

# استبدال هذه الدالة بواجهة الذكاء الاصطناعي الفعلية
def translate_text(text, source_lang, target_lang, api_key):
    # مثال باستخدام واجهة افتراضية (يجب استبدالها بالواجهة الحقيقية)
    return "النص المترجم هنا"

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()
