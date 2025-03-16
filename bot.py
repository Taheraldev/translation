import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pptx import Presentation
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display
from pptx.oxml.ns import qn

# دالة اختيارية لإعادة تشكيل النص العربي وعرضه بشكل صحيح
def fix_arabic(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# إعداد المترجم
translator = Translator()

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "مرحباً! أرسل لي ملف PPTX لترجمته مع الحفاظ على التنسيق قدر الإمكان."
    )

def handle_file(update: Update, context: CallbackContext):
    # تحميل الملف المرسل وحفظه محلياً
    file = update.message.document.get_file()
    local_input = "input.pptx"
    file.download(custom_path=local_input)
    
    # فتح الملف بواسطة python-pptx
    prs = Presentation(local_input)

    # اختر اللغة المصدر والهدف حسب الحاجة
    # يمكنك وضع src=None لاكتشاف اللغة تلقائياً
    src_lang = "en"   # لغة النص الأصلي (مثال: الإنجليزية)
    dest_lang = "ar"  # اللغة المراد الترجمة إليها (مثال: العربية)

    # المرور على جميع الشرائح وجميع الأشكال
    for slide in prs.slides:
        for shape in slide.shapes:
            # تأكد أن الشكل يحتوي على إطار نصي (TextFrame)
            if not shape.has_text_frame:
                continue
            
            text_frame = shape.text_frame
            
            # المرور على جميع الفقرات داخل TextFrame
            for paragraph in text_frame.paragraphs:
                original_text = paragraph.text.strip()
                if not original_text:
                    continue
                
                # يمكنك تنقية النص أو إصلاحه قبل الترجمة إذا أردت
                # مثلاً: original_text = fix_arabic(original_text) إذا كان النص عربي وتريد إعادة تشكيله
                
                # ترجمة كل فقرة بمفردها
                translated = translator.translate(original_text, src=src_lang, dest=dest_lang)
                new_text = translated.text

                # إذا كنت تترجم إلى العربية، قد تحتاج إلى إعادة تشكيل النص بعد الترجمة
                # new_text = fix_arabic(new_text)

                # تحديث نص الفقرة
                paragraph.text = new_text
            
            # بعد معالجة الفقرات، يمكننا ضبط اتجاه النص إلى RTL إذا كانت الوجهة العربية
            # (لتجنب تكرار الضبط لكل فقرة على حدة)
            if dest_lang == "ar":
                try:
                    bodyPr_elements = text_frame._element.xpath("./a:bodyPr")
                    if bodyPr_elements:
                        bodyPr = bodyPr_elements[0]
                        bodyPr.set(qn("a:rtl"), "1")
                except Exception as e:
                    print("Error setting RTL for a shape:", e)

    # حفظ الملف المُترجم
    output_file = "translated.pptx"
    prs.save(output_file)

    # إرسال الملف المترجم للمستخدم
    update.message.reply_document(document=open(output_file, 'rb'))

def main():
    # ضع توكن البوت الخاص بك
    updater = Updater("5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
