import os
import tempfile
import logging
import time
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import docx
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import arabic_reshaper
from bidi.algorithm import get_display
from googletrans import Translator
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# إعدادات الخط العربي
ARABIC_FONT = {
    'name': 'Arial',
    'size': Pt(12),
    'color': RGBColor(0x00, 0x00, 0x00)
}

# إعدادات المترجم
TRANSLATOR_CONFIG = {
    'service_urls': ['translate.google.com', 'translate.google.co.kr'],
    'retries': 3,
    'delay': 1,
    'timeout': 10
}

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("translation_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedTranslator:
    """فئة محسنة للتعامل مع مكتبة googletrans"""
    
    def __init__(self):
        self.translator = Translator()
        self.session = self.translator.session
    
    def translate_text(self, text):
        """ترجمة مع إدارة الأخطاء وإعادة المحاولة"""
        for attempt in range(TRANSLATOR_CONFIG['retries']):
            try:
                result = self.translator.translate(text, src='en', dest='ar')
                return result.text
            except Exception as e:
                logger.error(f"المحاولة {attempt+1} فشلت: {str(e)}")
                time.sleep(TRANSLATOR_CONFIG['delay'])
                self._reset_session()
        return text
    
    def _reset_session(self):
        """إعادة تعيين الجلسة لتجنب الحظر"""
        self.translator.session.close()
        self.translator.session = self.session = requests.Session()
        self.translator.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

def configure_rtl(paragraph):
    """تهيئة النص العربي"""
    paragraph._element.pPr.bidi = OxmlElement('w:bidi')
    paragraph._element.pPr.bidi.set(qn('w:val'), 'true')
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

def apply_arabic_style(run):
    """تطبيق إعدادات الخط"""
    run.font.name = ARABIC_FONT['name']
    run.font.size = ARABIC_FONT['size']
    run.font.color.rgb = ARABIC_FONT['color']

def process_arabic_text(text):
    """معالجة النص العربي"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def handle_docx(file_path):
    """معالجة ملفات الوورد"""
    doc = docx.Document(file_path)
    translator = AdvancedTranslator()
    
    for para in doc.paragraphs:
        if para.text.strip():
            translated = translator.translate_text(para.text)
            para.text = process_arabic_text(translated)
            configure_rtl(para)
            for run in para.runs:
                apply_arabic_style(run)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text.strip():
                        translated = translator.translate_text(para.text)
                        para.text = process_arabic_text(translated)
                        configure_rtl(para)
                        for run in para.runs:
                            apply_arabic_style(run)
    
    output_path = file_path.replace('.docx', '_translated.docx')
    doc.save(output_path)
    return output_path

def handle_pptx(file_path):
    """معالجة ملفات البوربوينت"""
    prs = Presentation(file_path)
    translator = AdvancedTranslator()
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    if paragraph.text.strip():
                        translated = translator.translate_text(paragraph.text)
                        processed_text = process_arabic_text(translated)
                        paragraph.text = processed_text
                        paragraph.alignment = PP_ALIGN.RIGHT
                        for run in paragraph.runs:
                            run.font.name = ARABIC_FONT['name']
                            run.font.size = ARABIC_FONT['size']
    
    output_path = file_path.replace('.pptx', '_translated.pptx')
    prs.save(output_path)
    return output_path

def start(update, context):
    """رسالة الترحيب"""
    welcome_msg = """
مرحبا بك في بوت الترجمة المجاني! 📚

🎯 الخدمات المدعومة:
- ترجمة ملفات DOCX/PPTX
- الحفاظ على التنسيق الأساسي
- دعم النصوص المعقدة

⚡ طريقة الاستخدام:
1. أرسل الملف مباشرة للبوت
2. انتظر حتى تنتهي المعالجة
3. استلم الملف المترجم

ملاحظات:
• الحد الأقصى لحجم الملف: 20MB
• تجنب الملفات المحمية
    """
    update.message.reply_text(welcome_msg)

def handle_file(update, context):
    """معالجة الملفات المرسلة"""
    output_path = None
    try:
        document = update.message.document
        filename = document.file_name.lower()
        file_path = os.path.join(tempfile.gettempdir(), filename)
        
        # تنزيل الملف
        context.bot.getFile(document.file_id).download(custom_path=file_path)
        update.message.reply_text("⚙️ جاري معالجة الملف...")
        
        # تحديد نوع الملف
        if filename.endswith('.docx'):
            output_path = handle_docx(file_path)
        elif filename.endswith('.pptx'):
            output_path = handle_pptx(file_path)
        else:
            update.message.reply_text("⚠️ نوع الملف غير مدعوم")
            return
        
        # إرسال الملف المترجم
        with open(output_path, 'rb') as f:
            context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                caption="✅ تمت الترجمة بنجاح"
            )
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        update.message.reply_text("❌ حدث خطأ أثناء المعالجة")
    finally:
        # تنظيف الملفات المؤقتة
        for f in [file_path, output_path]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                logger.warning(f"Error deleting file: {str(e)}")

def main():
    """الدالة الرئيسية"""
    TOKEN = "5146976580:AAE2yXc-JK6MIHVlLDy-O4YODucS_u7Zq-8"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
