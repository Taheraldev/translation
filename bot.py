import time
import logging
import groupdocs_translation_cloud
from groupdocs_translation_cloud import TextRequest, PdfFileRequest

# إعداد logging لتسجيل المعلومات على مستوى INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()
api.api_client.configuration.client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
api.api_client.configuration.client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

text_request = TextRequest(
    source_language="en",
    target_languages=["ru",],
    texts=["Hello World!", "This is a test text"],
    origin="your_application_name",
    contains_markdown=False
)
response = api.text_post(text_request)
if response.status == 202:
    while True:
        status_response = api.text_request_id_get(response.id)
        if status_response.status == 200:
            for lang in status_response.translations:
                # تسجيل الناتج في logs بدلاً من طباعته
                logging.info(f"{lang}: {status_response.translations[lang][0]}")
                break
        time.sleep(2)
