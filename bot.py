import time
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models import FileRequest, SavingMode

api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()

api.api_client.configuration.client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
api.api_client.configuration.client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# استخدام "Docx" بدلًا من "docx"
url = file_api.file_upload_post(file="yourfile.docx", format="Docx")
file_request = FileRequest(
    source_language="en",
    target_languages=["ru"],
    url=url,
    format="Docx",  # ✅ تصحيح التنسيق إلى القيمة الصحيحة
    saving_mode="Files",  # ✅ استخدام القيمة الصحيحة
    output_format="Docx"  # ✅ نفس التصحيح هنا
)

response = api.auto_post(file_request)
if response.status == 202:
    request_id = response.request_id  # استخراج request_id بشكل صحيح
    while True:
        file_response = api.document_request_id_get(request_id)
        if file_response.status == 200:
            print(file_response.message)
            for lang in file_response.urls:
                print(f"{lang}_{url}: {file_response.urls[lang].url}")
            break
        time.sleep(2)
