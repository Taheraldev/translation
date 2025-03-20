import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud import PdfFileRequest

# إعداد logging لعرض النتائج في logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# access token الذي حصلت عليه مسبقاً
access_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3NDI1MDU5ODUsImV4cCI6MTc0MjUwOTU4NSwiaXNzIjoiaHR0cHM6Ly9hcGkuZ3JvdXBkb2NzLmNsb3VkIiwiYXVkIjpbImh0dHBzOi8vYXBpLmdyb3VwZG9jcy5jbG91ZC9yZXNvdXJjZXMiLCJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl0sImNsaWVudF9pZCI6ImE5MWE2YWQxLTc2MzctNGU2NS1iNzkzLTQxYWY1NTQ1MDgwNyIsImNsaWVudF9kZWZhdWx0X3N0b3JhZ2UiOiJhNzA4ZTFhYS1hMjI1LTQxNjMtYWEwNS02YzE3MDU3NTUxMzQiLCJjbGllbnRfaWRlbnRpdHlfdXNlcl9pZCI6IjEwMjY4OTYiLCJzY29wZSI6WyJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl19.ZnZeuhyINlIURD8qvWYurH_eQzRfgUoRjxfZ_9q5p2K7a5oXDiC6eubua_b7v9L0HromhaLZK33CRKvraP_4KwdVX3MrUi5gvu1QABhZ9thxF1aRwhnnW49Q-5gkYtduD_vbVKqGdKcJYC8QZBRc0guZNtoNhE52nf-Z59xwMY-NPZm8ynQACI8z4-bDUVHPq15PPcpaSJzu2P4W3MB0EAHWNpU0pMJFh6XcbTgEdVxg5XnNxkzzvPBUiMLGkyvD-psaD20iqbzW7L9kxQX3bDb0Yk6k54ctIEjgdesv04J26e9NArih0aowhjNAYlMCXCmKKmRSSyPKFL01ieMB8g"

# تهيئة إعدادات GroupDocs مع استخدام access token
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
# تعيين الـ access token في الخاصية المخصصة له
configuration.access_token = access_token
# كما يمكنك تمرير token في مفتاح الـ API
configuration.api_key["access_token"] = access_token

# استخدام ApiClient مع إعداداتنا
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)

    # تحديد ملف PDF المراد ترجمته (تأكد من أن الملف موجود في المكان الصحيح)
    pdf_file_path = "file.pdf"

    # إنشاء طلب ترجمة PDF مع تحديد جميع المعلمات المطلوبة
    pdf_request = PdfFileRequest(
        file_path=pdf_file_path,
        sourceLanguage="en",           # اللغة المصدر
        target_languages=["ru"],       # قائمة اللغات الهدف
        outputFormat="pdf",            # صيغة الملف الناتج
        origin="my_translation_bot"    # تعريف مصدر الطلب
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
