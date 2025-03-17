import time
import groupdocs_translation_cloud
from groupdocs_translation_cloud.models import FileRequest, Format, SavingMode  # تعديل هنا

api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()
api.api_client.configuration.client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
api.api_client.configuration.client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

url = file_api.file_upload_post(file="/path/to/yourfile.docx", format=Format.Docx)
file_request = FileRequest(source_language="en", 
                           target_languages=["ru"], 
                           url=url, 
                           format=Format.Docx,
                           saving_mode=SavingMode.Files, 
                           output_format=Format.Docx)
response = api.auto_post(file_request)
if response.status == 202:
    request_id = response.request_id  # تأكد من استخراج request_id بالشكل الصحيح
    while True:
        file_response = api.document_request_id_get(request_id)
        if file_response.status == 200:
            print(file_response.message)
            for lang in file_response.urls:
                print(lang + '_' + url + ': ' + file_response.urls[lang].url)
            break
        time.sleep(2)
