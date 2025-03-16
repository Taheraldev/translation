import os
import logging
import openai
from pptx import Presentation
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد سجل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تعيين مفتاح OpenAI من متغير البيئة
openai.api_key = os.getenv("OPENAI_API_KEY")

def translate_text(text: str) -> str:
    """
    دالة تستخدم واجهة OpenAI لترجمة النص من الإنجليزية إلى العربية.
    """
    try:
        prompt = f"Please translate the following text from English to Arabic:\n\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        translation = response['choices'][0]['message']['content'].strip()
        return translation
    except Exception as e:
        logger.error(f"Translation error for text: {text}\nError: {e}")
        return text  # في حال حدوث خطأ، يُعيد النص الأصلي

def process_pptx(file_path: str, output_path: str):
    """
    تفتح هذه الدالة ملف البوربوينت وتترجم النصوص داخل كل فقرة
    ثم تحفظ الملف الجديد.
    """
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for paragraph in shape.text_frame.paragraphs:
                # دمج كل النصوص في الفقرة في متغير واحد
                full_text = "".join(run.text for run in paragraph.runs if run.text.strip())
                if full_text.strip():
                    translated = translate_text(full_text)
                    # تحديث الفقرة: وضع الترجمة في أول run وتفريغ الباقي
                    if paragraph.runs:
                        paragraph.runs[0].text = translated
                        for run in paragraph.runs[1:]:
                            run.text = ""
    prs.save(output_path)

def start(update: Update, context: CallbackContext):
    """
    رسالة ترحيب عند بدء التفاعل مع البوت.
    """
    update.message.reply_text("مرحباً! أرسل لي ملف بوربوينت (.pptx) وسأقوم بترجمته من الإنجليزية إلى العربية.")

def handle_document(update: Update, context: CallbackContext):
    """
    يستقبل البوت ملف بوربوينت ويعالجه للترجمة ثم يرسله مرة أخرى.
    """
    document = update.message.document
    file_name = document.file_name

    if not file_name.lower().endswith(".pptx"):
        update.message.reply_text("يرجى إرسال ملف بوربوينت بامتداد .pptx")
        return

    os.makedirs("downloads", exist_ok=True)
    input_file_path = os.path.join("downloads", file_name)
    output_file_path = os.path.join("downloads", f"translated_{file_name}")

    file = context.bot.get_file(document.file_id)
    file.download(custom_path=input_file_path)
    update.message.reply_text("جاري معالجة الملف، يرجى الانتظار...")

    try:
        process_pptx(input_file_path, output_file_path)
        with open(output_file_path, 'rb') as f:
            update.message.reply_document(document=InputFile(f, filename=f"translated_{file_name}"))
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        update.message.reply_text("حدث خطأ أثناء ترجمة الملف، يرجى المحاولة مرة أخرى.")

def main():
    # تعيين مفتاح بوت Telegram من متغير البيئة
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
