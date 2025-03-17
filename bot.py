import os
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.presentation_file_request import PresentationFileRequest
from groupdocs_translation_cloud.models.translation_options import TranslationOptions
from groupdocs_translation_cloud.rest import ApiException
from pprint import pprint

# تهيئة إعدادات API
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = os.environ["ACCESS_TOKEN"]

# إعداد معلمات الترجمة مع تحديد الملف واللغات
translation_options = TranslationOptions(
    file_info={"file_path": "Section 5d.pptx", "password": ""},  # عدل مسار الملف حسب مكانه
    source_language="en",    # اللغة الأصلية
    target_language="ar"     # اللغة الهدف
)

# إنشاء طلب الترجمة باستخدام الخيارات المحددة
presentation_file_request = PresentationFileRequest(translation_options=translation_options)

# استخدام العميل لاستدعاء الدالة التي تقوم بترجمة الملف
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)
    try:
        # ترجمة الملف
        api_response = api_instance.presentation_post(presentation_file_request=presentation_file_request)
        print("نتيجة عملية الترجمة:")
        pprint(api_response)
    except ApiException as e:
        print("حدث استثناء عند استدعاء TranslationApi->presentation_post: %s\n" % e)
