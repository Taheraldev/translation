import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pptx import Presentation
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display

# دالة لتعديل النص العربي لعرضه بشكل صحيح (اختيارية)
def fix_arabic(text):
    # تعيد تشكيل الحروف العربية
    reshaped_text = arabic_reshaper.reshape(text)
    # تطبيق خوارزمية bidi لضبط اتجاه النص
    bidi_text = get_display(reshaped_text)
    return bidi_text

# إعداد المترجم
translator = Translator()

# دالة بدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! أرسل لي ملف PPTX للترجمة من العربية إلى الإنجليزية.")

# دالة التعامل مع ملف PPTX
def handle_file(update: Update, context: CallbackContext):
    # تحميل الملف المرسل وحفظه محلياً
    file = update.message.document.get_file()
    local_input = "input.pptx"
    file.download(custom_path=local_input)
    
    # فتح الملف باستخدام python-pptx
    prs = Presentation(local_input)
    
    # المرور على كل الشريحة وكل شكل في الشرائح
    for slide in prs.slides:
        for shape in slide.shapes:
            # التأكد من أن الشكل يحتوي على نص
            if hasattr(shape, "text") and shape.text.strip():
                original_text = shape.text.strip()
                # إزالة الفراغات الزائدة وتنقية النص
                refined_text = " ".join(original_text.split())
                
                # ملحوظة: إذا رغبت في عرض النص العربي بشكل صحيح في بعض الحالات،
                # يمكنك استخدام الدالة fix_arabic على النص الأصلي.
                # على سبيل المثال:
                # refined_text = fix_arabic(refined_text)
                # لكن يُفضل إرسال النص المنطقي (غير المعكوس) إلى خدمة الترجمة.
                
                # ترجمة النص من العربية إلى الإنجليزية
                translated = translator.translate(refined_text, src="en", dest="ar")
                shape.text = translated.text

                # محاولة تعديل اتجاه النص ليكون من اليمين إلى اليسار (RTL)
                try:
                    if shape.has_text_frame:
                        from pptx.oxml.ns import qn
                        # الوصول لعنصر bodyPr الخاص بتنسيق النص داخل shape
                        bodyPr_elements = shape.text_frame._element.xpath("./a:bodyPr")
                        if bodyPr_elements:
                            bodyPr = bodyPr_elements[0]
                            # تعيين خاصية RTL للقيمة 1
                            bodyPr.set(qn("a:rtl"), "1")
                except Exception as e:
                    # في حال حدوث خطأ أثناء تعديل اتجاه النص، يتم طباعته دون تعطيل البوت
                    print("Error setting RTL for a shape:", e)
    
    # حفظ الملف الجديد بعد الترجمة
    output_file = "translated.pptx"
    prs.save(output_file)
    
    # إرسال الملف المُترجم للمستخدم
    update.message.reply_document(document=open(output_file, 'rb'))

def main():
    # ضع توكن البوت الخاص بك هنا
    updater = Updater("5146976580:AAFHTu1ZQQjVlKHtYY2V6L9sRu4QxrHaA2A", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
