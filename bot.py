from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update, InputFile
import os
import fitz
from apify_client import ApifyClient

# إعدادات Apify
APIFY_API_KEY = "apify_api_f3RTo40c6qrsfZmg9Fw4fIvkZgpgU50ausCM"
ACTOR_ID = "web.harvester/reverso-translator"

# إعدادات البوت
TOKEN = "5146976580:AAH0ZpK52d6fKJY04v-9mRxb6Z1fTl0xNLw"

def start(update: Update, context):
    update.message.reply_text('مرحبا! أرسل ملف PDF لترجمته إلى الإنجليزية.')

def handle_pdf(update: Update, context):
    try:
        # تنزيل الملف
        file = update.message.document.get_file()
        downloaded_file = file.download(custom_path="input.pdf")
        
        # معالجة الملف
        translated_pdf = process_pdf(downloaded_file)
        
        # إرسال الملف المترجم
        with open(translated_pdf, 'rb') as f:
            update.message.reply_document(document=InputFile(f, filename="translated.pdf"))
        
    except Exception as e:
        update.message.reply_text(f'حدث خطأ: {str(e)}')
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if os.path.exists(translated_pdf):
            os.remove(translated_pdf)

def process_pdf(input_path):
    # استخراج النصوص ومواقعها
    text_blocks = extract_text_with_positions(input_path)
    
    # ترجمة النصوص
    translated_blocks = translate_texts(text_blocks)
    
    # إنشاء PDF جديد
    output_path = "translated_output.pdf"
    create_translated_pdf(output_path, translated_blocks)
    
    return output_path

def extract_text_with_positions(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []
    
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_data.append({
                            "text": span["text"],
                            "page": page_num,
                            "bbox": span["bbox"],
                            "fontsize": span["size"],
                            "fontname": span["font"]
                        })
    return text_data

def translate_texts(text_blocks):
    client = ApifyClient(APIFY_API_KEY)
    
    # إعداد بيانات الترجمة لـ Reverso
    run_input = {
        "texts": [tb["text"] for tb in text_blocks],
        "sourceLang": "ar",
        "targetLang": "en",
        "detailedResults": True
    }
    
    try:
        # تشغيل مهمة الترجمة
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        
        # استخراج النتائج
        translated_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        # دمج النتائج مع البيانات الأصلية
        for i, tb in enumerate(text_blocks):
            if i < len(translated_items):
                tb["translated_text"] = translated_items[i].get("translation", "")
            else:
                tb["translated_text"] = "[ترجمة غير متوفرة]"
        
        return text_blocks
    except Exception as e:
        raise Exception(f"فشل في الترجمة: {str(e)}")

def create_translated_pdf(output_path, translated_blocks):
    doc = fitz.open()
    
    current_page = -1
    page = None
    
    for block in translated_blocks:
        if block["page"] != current_page:
            page = doc.new_page(-1, width=612, height=792)
            current_page = block["page"]
        
        # الحفاظ على التنسيق الأصلي
        rc = block["bbox"]
        try:
            page.insert_text(
                point=(rc[0], rc[1]),
                text=block["translated_text"],
                fontname=block["fontname"],
                fontsize=block["fontsize"],
                color=(0, 0, 0)
            )
        except:
            # استخدام خط افتراضي إذا كان الخط غير متوفر
            page.insert_text(
                point=(rc[0], rc[1]),
                text=block["translated_text"],
                fontname="helv",
                fontsize=block["fontsize"],
                color=(0, 0, 0)
            )
    
    doc.save(output_path)

if __name__ == "__main__":
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))
    
    updater.start_polling()
    updater.idle()
