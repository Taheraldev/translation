import os
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models import PresentationFileRequest
from groupdocs_translation_cloud.rest import ApiException
from pprint import pprint

# تهيئة إعدادات API
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = os.environ.get("ACCESS_TOKEN")  # تأكد من تعيين المتغير في البيئة

# تحديد بيانات الملف واللغة
presentation_file_request = PresentationFileRequest(
    file_info={"file_path": "Section 5d.pptx", "password": ""},  # ضع مسار ملفك هنا
    source_language="en",  # اللغة الأصلية
    target_language="ar"   # اللغة المستهدفة
)

# استخدام API لترجمة الملف
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)
    try:
        api_response = api_instance.presentation_post(presentation_file_request=presentation_file_request)
        print("تمت الترجمة بنجاح! 🚀")
        pprint(api_response)
    except ApiException as e:
        print(f"حدث خطأ أثناء الترجمة: {e}")
