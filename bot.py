import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud import PdfFileRequest

# إعداد logging لعرض النتائج في logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# access token الذي حصلت عليه مسبقاً
access_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3NDI1MDc2NDQsImV4cCI6MTc0MjUxMTI0NCwiaXNzIjoiaHR0cHM6Ly9hcGkuZ3JvdXBkb2NzLmNsb3VkIiwiYXVkIjpbImh0dHBzOi8vYXBpLmdyb3VwZG9jcy5jbG91ZC9yZXNvdXJjZXMiLCJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl0sImNsaWVudF9pZCI6ImE5MWE2YWQxLTc2MzctNGU2NS1iNzkzLTQxYWY1NTQ1MDgwNyIsImNsaWVudF9kZWZhdWx0X3N0b3JhZ2UiOiJhNzA4ZTFhYS1hMjI1LTQxNjMtYWEwNS02YzE3MDU3NTUxMzQiLCJjbGllbnRfaWRlbnRpdHlfdXNlcl9pZCI6IjEwMjY4OTYiLCJzY29wZSI6WyJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl19.8jN9cyGeih_dMJKBCaiTBfa0y3VXaDL5lvVULfzB4u7g2fAVrBmxxS9qnR_jKJdhyqRpURBVEP4EIwGjk9BF1VH4ucIWMyKBYxVuXociVD4dQeXa5sdYMlmd43BJtnQ-WnYAgiY5zeWhgLyhJ19EgKq16ZZLlQKyqtH7-3S2pKtE4p_34ijqpk5utlzbL_N75bNqgRCH4x3Vk7Lq64bR2F_idPI4r2qPrX-XfPLXelMJn_ulljb3-zAqvZp-l7PIaUm4eKkrP1DEf7tehg7oItXmw4EskuXI6uCn-ctqESkGCbRDbGUZAzsS2NmjN_MIQRteGb4mXseG-hbp6a3HTg"

# تهيئة إعدادات GroupDocs مع استخدام access token مباشرة
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
# تعيين الـ access token مباشرة
configuration.access_token = access_token

# تعيين الـ api_key باستخدام الـ access token، وتحديد بادئتها Bearer
configuration.api_key = {"access_token": access_token}
configuration.api_key_prefix = {"access_token": "Bearer"}

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
