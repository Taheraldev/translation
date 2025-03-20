import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud import PdfFileRequest

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تهيئة API
api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()
api.api_client.configuration.client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
api.api_client.configuration.client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# تحديد ملف PDF المراد ترجمته
pdf_file_path = "file.pdf"  # استبدل هذا بالمسار الصحيح للملف

# إنشاء طلب ترجمة PDF مع تحديد sourceLanguage و outputFormat
pdf_request = PdfFileRequest(
    file_path=pdf_file_path,
    target_languages=["ar"],       # اللغات الهدف
    sourceLanguage="en",           # اللغة المصدر (مثلاً الإنجليزية)
    outputFormat="pdf",            # تنسيق الملف الناتج
    origin="your_application_name"
)

# إرسال الطلب
response = api.pdf_post(pdf_request)

if response.status == 202:
    while True:
        status_response = api.pdf_request_id_get(response.id)
        if status_response.status == 200:
            translated_file_path = status_response.translations["ar"]
            logging.info(f"تمت الترجمة! رابط الملف المترجم: {translated_file_path}")

            # تنزيل الملف المترجم
            output_path = "translated_file.pdf"
            file_api.download_file(translated_file_path, output_path)
            logging.info(f"تم تنزيل الملف المترجم وحفظه في: {output_path}")
            break
        time.sleep(2)
