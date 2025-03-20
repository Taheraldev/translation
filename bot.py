import os
import time
import logging
import requests
import groupdocs_translation_cloud
from groupdocs_translation_cloud import PdfFileRequest

# إعداد logging لعرض النتائج في logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# بيانات الاعتماد الخاصة بك
client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# عنوان endpoint لإنشاء access token
token_url = "https://api.groupdocs.cloud/connect/token"

# إعداد البيانات المطلوبة للطلب
payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# الحصول على access token
logging.info("🚀 الحصول على access token...")
token_response = requests.post(token_url, data=payload)
if token_response.status_code == 200:
    access_token = token_response.json().get("access_token")
    logging.info("✅ access token تم الحصول عليه بنجاح!")
else:
    logging.error(f"❌ فشل الحصول على access token، رمز الحالة: {token_response.status_code}")
    exit(1)

# تهيئة إعدادات GroupDocs مع استخدام access token
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = access_token

# استخدام ApiClient مع إعداداتنا
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)

    # تحديد ملف PDF المراد ترجمته
    pdf_file_path = "file.pdf"  # تأكد أن المسار صحيح والملف موجود

    # إنشاء طلب ترجمة PDF
    pdf_request = PdfFileRequest(
        file_path=pdf_file_path,
        sourceLanguage="en",           # اللغة المصدر (مثلاً: الإنجليزية)
        target_languages=["ru"],       # قائمة اللغات الهدف (مثلاً: العربية)
        outputFormat="pdf",            # صيغة الملف الناتج
        origin="my_translation_bot"    # يمكن تعديلها أو حذفها
    )

    try:
        logging.info("🚀 إرسال طلب الترجمة لملف PDF...")
        response = api_instance.pdf_post(pdf_file_request=pdf_request)

        if response.status == 202:
            logging.info(f"✅ الطلب قيد التنفيذ، معرف الطلب: {response.id}")

            while True:
                status_response = api_instance.pdf_request_id_get(response.id)
                if status_response.status == 200:
                    translated_file_path = status_response.translations["ru"]
                    logging.info(f"🎯 تمت الترجمة! رابط الملف المترجم: {translated_file_path}")

                    # تنزيل الملف المترجم
                    output_path = "translated_file.pdf"
                    file_api = groupdocs_translation_cloud.api.FileApi(api_client)
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
