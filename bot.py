import os
import tempfile
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import docx
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from googletrans import Translator
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import arabic_reshaper
from bidi.algorithm import get_display
from convertapi import ConvertApi

# إعداد ConvertApi بمفتاحه السري
ConvertApi.secret = 'secret_q4ijKpkWw17sLQx8'

# إعداد الـ logging لتتبع الأخطاء والعمليات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# قواميس لتخزين أوضاع المستخدم والملفات المعلقة لتحويل PDF
conversion_mode = {}          # مثلاً: { user_id: 'to_pdf' } عندما يرسل المستخدم أمر /pdf
pending_pdf_conversion = {}   # لتخزين مسار ملف PDF المعلق عند إرسال ملف PDF

# تهيئة المترجم
translator = Translator()

def set_paragraph_rtl(paragraph):
    """
    تضيف هذه الدالة عنصر XML لتعيين اتجاه الفقرة من اليمين إلى اليسار.
    """
    p = paragraph._p
    pPr = p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr')
        p.insert(0, pPr)
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), "1")
    pPr.append(bidi)

def process_arabic_text(text):
    """
    تعالج النص العربي باستخدام arabic_reshaper و python-bidi ليظهر بالشكل الصحيح.
    """
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def translate_docx(file_path):
    """
    تفتح ملف DOCX وتترجم نصوصه (بما في ذلك داخل الجداول)، مع ضبط اتجاه النص.
    """
    doc = docx.Document(file_path)
    
    # ترجمة الفقرات العادية
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip():
                try:
                    translated = translator.translate(run.text, src='en', dest='ar')
                    run.text = process_arabic_text(translated.text)
                except Exception as e:
                    logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
        set_paragraph_rtl(para)
    
    # ترجمة النصوص داخل الجداول
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص داخل الجدول: {run.text}. الخطأ: {e}")
                    set_paragraph_rtl(para)
    
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def translate_pptx(file_path):
    """
    تفتح ملف PPTX وتترجم النصوص داخل الشرائح مع ضبط محاذاة النص إلى اليمين.
    """
    prs = Presentation(file_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text_frame") and shape.text_frame is not None:
                for paragraph in shape.text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.RIGHT
                    for run in paragraph.runs:
                        if run.text.strip():
                            try:
                                translated = translator.translate(run.text, src='en', dest='ar')
                                run.text = process_arabic_text(translated.text)
                            except Exception as e:
                                logger.error(f"خطأ أثناء ترجمة النص: {run.text}. الخطأ: {e}")
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def perform_conversion(input_path, target_format):
    """
    تقوم هذه الدالة بتحويل الملف باستخدام ConvertApi إلى الصيغة المطلوبة.
    يُحدد اسم الملف الناتج بناءً على مسار الملف الأصلي.
    """
    output_path = input_path.rsplit('.', 1)[0] + f'_converted.{target_format}'
    result = ConvertApi().convert(target_format, {'File': input_path})
    # يتم حفظ الملف الناتج؛ اعتماداً على واجهة ConvertApi يمكن أن يكون save_files قادر على حفظ الملف مباشرة بالاسم المحدد
    result.save_files(output_path)
    return output_path

def handle_document(update, context):
    user_id = update.message.from_user.id
    document = update.message.document
    filename = document.file_name.lower()
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # تنزيل الملف إلى مجلد مؤقت
    file = context.bot.getFile(document.file_id)
    file.download(custom_path=file_path)
    
    # حالة تحويل إلى PDF (عند إرسال أمر /pdf)
    if conversion_mode.get(user_id) == 'to_pdf':
        if filename.endswith('.docx') or filename.endswith('.pptx'):
            try:
                converted_path = perform_conversion(file_path, 'pdf')
                caption_text = "تم تحويل الملف إلى PDF بنجاح!"
                context.bot.send_document(chat_id=update.message.chat_id, document=open(converted_path, 'rb'), caption=caption_text)
            except Exception as e:
                logger.error(f"Error converting to PDF: {e}")
                update.message.reply_text("❌ فشل التحويل إلى PDF.")
            finally:
                conversion_mode.pop(user_id, None)
                if os.path.exists(file_path):
                    os.remove(file_path)
                if os.path.exists(converted_path):
                    os.remove(converted_path)
            return
        else:
            update.message.reply_text("❌ صيغة الملف غير مدعومة للتحويل إلى PDF.")
            conversion_mode.pop(user_id, None)
            if os.path.exists(file_path):
                os.remove(file_path)
            return

    # إذا كان الملف PDF، نعرض للمستخدم خيارات التحويل باستخدام InlineKeyboardButton
    if filename.endswith('.pdf'):
        pending_pdf_conversion[user_id] = file_path
        keyboard = [
            [
                InlineKeyboardButton("DOCX", callback_data="pdf_conv:docx"),
                InlineKeyboardButton("PPTX", callback_data="pdf_conv:pptx")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر الصيغة لتحويل PDF:", reply_markup=reply_markup)
        return
    
    # إذا كان الملف DOCX أو PPTX نقوم بالترجمة
    if filename.endswith('.docx'):
        try:
            translated_path = translate_docx(file_path)
            context.bot.send_document(chat_id=update.message.chat_id, document=open(translated_path, 'rb'), caption="تم ترجمة الملف بنجاح!")
        except Exception as e:
            logger.error(f"Error translating DOCX: {e}")
            update.message.reply_text("❌ حدث خطأ أثناء ترجمة الملف.")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(translated_path):
                os.remove(translated_path)
        return
    elif filename.endswith('.pptx'):
        try:
            translated_path = translate_pptx(file_path)
            context.bot.send_document(chat_id=update.message.chat_id, document=open(translated_path, 'rb'), caption="تم ترجمة الملف بنجاح!")
        except Exception as e:
            logger.error(f"Error translating PPTX: {e}")
            update.message.reply_text("❌ حدث خطأ أثناء ترجمة الملف.")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(translated_path):
                os.remove(translated_path)
        return
    elif filename.endswith('.doc'):
        update.message.reply_text("صيغة DOC غير مدعومة مباشرة. الرجاء تحويل الملف إلى DOCX أولاً (يمكن استخدام LibreOffice للتحويل).")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    elif filename.endswith('.ppt'):
        update.message.reply_text("صيغة PPT غير مدعومة مباشرة. الرجاء تحويل الملف إلى PPTX أولاً (يمكن استخدام LibreOffice للتحويل).")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    else:
        update.message.reply_text("صيغة الملف غير مدعومة.")
        if os.path.exists(file_path):
            os.remove(file_path)
        return

def pdf_conversion_callback(update, context):
    """
    يتعامل هذا المُعالج مع نقر المستخدم على زر تحويل PDF،
    فيقوم بتحويل الملف إلى الصيغة المطلوبة (DOCX أو PPTX) باستخدام ConvertApi.
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data  # الصيغة تكون بالشكل "pdf_conv:docx" أو "pdf_conv:pptx"
    
    if user_id not in pending_pdf_conversion:
        query.answer("لم يعد الملف متاحاً.")
        return
    
    input_path = pending_pdf_conversion.pop(user_id)
    target_format = data.split(":")[1]
    try:
        output_path = perform_conversion(input_path, target_format)
        query.message.reply_document(document=open(output_path, 'rb'),
                                     caption=f"تم تحويل PDF إلى {target_format.upper()} بنجاح!")
    except Exception as e:
        logger.error(f"Error converting PDF to {target_format}: {e}")
        query.message.reply_text("❌ فشل التحويل.")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
    query.answer()

def pdf_command(update, context):
    """
    عند إرسال أمر /pdf، يُدخل البوت المستخدم في وضع تحويل DOCX/PPTX إلى PDF.
    """
    user_id = update.message.from_user.id
    conversion_mode[user_id] = 'to_pdf'
    update.message.reply_text("أرسل لي ملف DOCX أو PPTX لتحويله إلى PDF.")

def start(update, context):
    """
    رسالة الترحيب توضح وظائف البوت المتعددة.
    """
    welcome_text = (
        "مرحباً! أنا بوت متعدد الوظائف:\n\n"
        "1. ترجمة ملفات DOCX و PPTX من الإنجليزية إلى العربية.\n"
        "2. تحويل ملفات PDF إلى DOCX أو PPTX (اختر الصيغة باستخدام الأزرار) عند إرسال الملف.\n"
        "3. تحويل ملفات DOCX أو PPTX إلى PDF عند إرسال أمر /pdf مع الملف.\n\n"
        "ملاحظة: صيغة DOC و PPT غير مدعومة مباشرة؛ الرجاء تحويلها إلى DOCX أو PPTX."
    )
    update.message.reply_text(welcome_text)

def main():
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("pdf", pdf_command))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_handler(CallbackQueryHandler(pdf_conversion_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
