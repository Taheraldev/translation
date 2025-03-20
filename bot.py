import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud import PdfFileRequest

# إعداد logging لعرض النتائج في logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تهيئة API
api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()

# استبدل التوكنات ببيانات الاعتماد الخاصة بك
api.api_client.configuration.client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
api.api_client.configuration.client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# تحديد ملف PDF المراد ترجمته
pdf_file_path = "file.pdf"  # استبدل بالمسار الصحيح للملف

# إنشاء طلب ترجمة PDF
pdf_request = PdfFileRequest(
    file_path=pdf_file_path,
    sourceLanguage="en",           # لغة المصدر (مثلاً: الإنجليزية)
    target_languages=["ru"],       # اللغات المستهدفة (العربية هنا)
    outputFormat="pdf",            # صيغة الملف الناتج (PDF)
    origin="your_application_name"
)

try:
    logging.info("🚀 إرسال طلب الترجمة...")
    response = api.pdf_post(pdf_request)

    if response.status == 202:
        logging.info(f"✅ الطلب قيد التنفيذ، معرف الطلب: {response.id}")

        while True:
            # التحقق من حالة الترجمة
            status_response = api.pdf_request_id_get(response.id)
            if status_response.status == 200:
                translated_file_path = status_response.translations["ru"]
                logging.info(f"🎯 تمت الترجمة! رابط الملف المترجم: {translated_file_path}")

                # تنزيل الملف المترجم
                output_path = "translated_file.pdf"
                file_api.download_file(translated_file_path, output_path)
                logging.info(f"📥 تم تنزيل الملف المترجم وحفظه في: {output_path}")
                break
            else:
                logging.info("⏳ الترجمة قيد التنفيذ... الرجاء الانتظار")
            time.sleep(2)
    else:
        logging.error(f"❌ فشل في إرسال الطلب! حالة الاستجابة: {response.status}")

except groupdocs_translation_cloud.exceptions.ServiceException as e:
    logging.error(f"❌ خطأ في الخدمة: {e}")
except Exception as e:
    logging.error(f"⚠️ حدث خطأ غير متوقع: {e}")
