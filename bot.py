import os
import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.presentation_file_request import PresentationFileRequest
from groupdocs_translation_cloud.rest import ApiException
from pprint import pprint

# إعداد logging لعرض الرسائل في السجل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تأكد من تعيين متغير البيئة ACCESS_TOKEN أو استبدله بالتوكن الخاص بك مباشرة
access_token = os.environ.get("ACCESS_TOKEN", "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3NDI1MDc2NDQsImV4cCI6MTc0MjUxMTI0NCwiaXNzIjoiaHR0cHM6Ly9hcGkuZ3JvdXBkb2NzLmNsb3VkIiwiYXVkIjpbImh0dHBzOi8vYXBpLmdyb3VwZG9jcy5jbG91ZC9yZXNvdXJjZXMiLCJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl0sImNsaWVudF9pZCI6ImE5MWE2YWQxLTc2MzctNGU2NS1iNzkzLTQxYWY1NTQ1MDgwNyIsImNsaWVudF9kZWZhdWx0X3N0b3JhZ2UiOiJhNzA4ZTFhYS1hMjI1LTQxNjMtYWEwNS02YzE3MDU3NTUxMzQiLCJjbGllbnRfaWRlbnRpdHlfdXNlcl9pZCI6IjEwMjY4OTYiLCJzY29wZSI6WyJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl19.8jN9cyGeih_dMJKBCaiTBfa0y3VXaDL5lvVULfzB4u7g2fAVrBmxxS9qnR_jKJdhyqRpURBVEP4EIwGjk9BF1VH4ucIWMyKBYxVuXociVD4dQeXa5sdYMlmd43BJtnQ-WnYAgiY5zeWhgLyhJ19EgKq16ZZLlQKyqtH7-3S2pKtE4p_34ijqpk5utlzbL_N75bNqgRCH4x3Vk7Lq64bR2F_idPI4r2qPrX-XfPLXelMJn_ulljb3-zAqvZp-l7PIaUm4eKkrP1DEf7tehg7oItXmw4EskuXI6uCn-ctqESkGCbRDbGUZAzsS2NmjN_MIQRteGb4mXseG-hbp6a3HTg")

# تهيئة إعدادات GroupDocs مع تحديد host الخاص بالـ API
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = access_token

# يمكنك إذا رغبت تعيين access token في مفتاح api_key أيضًا (حسب الحاجة)
configuration.api_key = {"access_token": access_token}
configuration.api_key_prefix = {"access_token": "Bearer"}

# إنشاء عميل API واستخدامه في سياق with لإدارة الاتصال
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)
    
    # إعداد طلب ترجمة ملف العرض التقديمي
    # تأكد من أن الملف موجود في المسار المحدد وأن بقية المعلمات صحيحة
    presentation_request = PresentationFileRequest(
        file_path="presentation.pptx",  # استبدل بمسار ملف العرض التقديمي الذي تريد ترجمته
        sourceLanguage="en",            # اللغة المصدر
        target_languages=["ru"],        # قائمة اللغات الهدف (يمكنك إضافة لغات أخرى داخل القائمة)
        outputFormat="pptx",            # صيغة الملف الناتج؛ مثلاً pptx أو odp
        origin="my_presentation_translator"  # معرّف تطبيقك أو اسم مشروعك
    )
    
    try:
        logging.info("🚀 إرسال طلب ترجمة ملف العرض التقديمي...")
        api_response = api_instance.presentation_post(presentation_file_request=presentation_request)
        
        if api_response.status == 202:
            logging.info(f"✅ الطلب قيد التنفيذ، معرف الطلب: {api_response.id}")
            
            # الانتظار حتى تنتهي عملية الترجمة؛ يمكنك تعديل فترة الانتظار كما تشاء
            while True:
                status_response = api_instance.presentation_request_id_get(api_response.id)
                if status_response.status == 200:
                    translated_file_path = status_response.translations["ru"]
                    logging.info(f"🎯 تمت الترجمة! رابط الملف المترجم: {translated_file_path}")
                    
                    # يمكنك تنزيل الملف المترجم باستخدام FileApi أو أي طريقة تناسب احتياجاتك
                    break
                else:
                    logging.info("⏳ الترجمة قيد التنفيذ... الرجاء الانتظار")
                time.sleep(2)
        else:
            logging.error(f"❌ فشل في إرسال الطلب! حالة الاستجابة: {api_response.status}")
    except ApiException as e:
        logging.error(f"❌ Exception when calling TranslationApi->presentation_post: {e}")
    except Exception as e:
        logging.error(f"⚠️ حدث خطأ غير متوقع: {e}")
