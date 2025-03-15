import logging
import os
import time
import base64
import json
import requests
import chardet
from datetime import date
import PyPDF2
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup, NavigableString
import mtranslate
import arabic_reshaper
from bidi.algorithm import get_display
from docx import Document
from pptx import Presentation
import pdfcrowd
import io

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد التوكن ومفاتيح API
TELEGRAM_TOKEN = '7912949647:AAFOPvPuWtU6fyZNUCa08WuU9KVXJZZiXMM'
CONVERTIO_API = 'https://api.convertio.co/convert'
CONVERTIO_API_KEY = '3c50e707584d2cbe0139d35033b99d7c'

# بيانات PDFCrowd (لتحويل HTML إلى PDF)
PDFCROWD_USERNAME = "taherja"
PDFCROWD_API_KEY = "4f59bd9b2030deabe9d14c92ed65817a"

# إعداد ملف بيانات المستخدمين ومعرف الإدارة
USER_FILE = "user_data.json"
ADMIN_CHAT_ID = 5198110160

# لتتبع عدد الملفات المحولة يومياً لكل مستخدم (user_id: (last_date, count))
user_file_usage = {}

def load_user_data():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                logger.error(f"Error loading user data: {e}")
                return {}
    return {}

def save_user_data(data):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def fix_arabic(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def translate_text_group(text_group):
    marker = "<<<SEP>>>"
    combined = marker.join(segment.strip() for segment in text_group)
    try:
        translated_combined = mtranslate.translate(combined, 'ar', 'en')
        translated_combined = fix_arabic(translated_combined)
    except Exception as e:
        logger.error(f"خطأ أثناء ترجمة المجموعة: {e}")
        translated_combined = None

    if translated_combined:
        parts = translated_combined.split(marker)
        if len(parts) == len(text_group):
            final_parts = []
            for orig, part in zip(text_group, parts):
                leading_spaces = orig[:len(orig) - len(orig.lstrip())]
                trailing_spaces = orig[len(orig.rstrip()):]
                final_parts.append(leading_spaces + part + trailing_spaces)
            return final_parts

    result = []
    for segment in text_group:
        try:
            t = mtranslate.translate(segment.strip(), 'ar', 'en')
            t = fix_arabic(t)
        except Exception as e:
            logger.error(f"خطأ أثناء ترجمة الجزء: {e}")
            t = segment
        leading_spaces = segment[:len(segment) - len(segment.lstrip())]
        trailing_spaces = segment[len(segment.rstrip()):]
        result.append(leading_spaces + t + trailing_spaces)
    return result

def process_parent_texts(parent):
    new_contents = []
    group = []
    for child in parent.contents:
        if isinstance(child, NavigableString):
            group.append(str(child))
        else:
            if group:
                translated_group = translate_text_group(group)
                for text in translated_group:
                    new_contents.append(NavigableString(text))
                group = []
            new_contents.append(child)
    if group:
        translated_group = translate_text_group(group)
        for text in translated_group:
            new_contents.append(NavigableString(text))
    parent.clear()
    for item in new_contents:
        parent.append(item)

def translate_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    head = soup.find('head')
    if head and not head.find('meta', charset=True):
        meta_tag = soup.new_tag('meta', charset='UTF-8')
        head.insert(0, meta_tag)
    
    for tag in soup.find_all():
        if tag.name in ['script', 'style']:
            continue
        if any(isinstance(child, NavigableString) and child.strip() for child in tag.contents):
            process_parent_texts(tag)
    
    return str(soup)

def translate_docx(input_path, output_path, progress_callback=None):
    doc = Document(input_path)
    total = len(doc.paragraphs) if doc.paragraphs else 1
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            try:
                translated = mtranslate.translate(para.text, 'ar', 'en')
                translated = fix_arabic(translated)
                para.text = translated
            except Exception as e:
                logger.error(f"Error translating DOCX paragraph: {e}")
        if progress_callback:
            progress_callback(int(((i+1) / total) * 100))
    doc.save(output_path)

def translate_pptx(input_path, output_path, progress_callback=None):
    prs = Presentation(input_path)
    shapes_list = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                shapes_list.append(shape)
    total = len(shapes_list) if shapes_list else 1
    for i, shape in enumerate(shapes_list):
        try:
            translated = mtranslate.translate(shape.text, 'ar', 'en')
            translated = fix_arabic(translated)
            shape.text = translated
        except Exception as e:
            logger.error(f"Error translating PPTX shape: {e}")
        if progress_callback:
            progress_callback(int(((i+1) / total) * 100))
    prs.save(output_path)

def convert_html_to_pdf(html_content: str) -> bytes:
    try:
        client = pdfcrowd.HtmlToPdfClient(PDFCROWD_USERNAME, PDFCROWD_API_KEY)
        output_stream = io.BytesIO()
        client.convertStringToStream(html_content, output_stream)
        output_stream.seek(0)
        return output_stream.read()
    except pdfcrowd.Error as e:
        logger.error("PDFCrowd Error: %s", e)
        return None

# باقي الدوال (handle_document, start, main) تبقى كما هي بدون تغيير
# ... [يجب نسخها كما هي من الكود الأصلي] ...

if __name__ == '__main__':
    main()      
