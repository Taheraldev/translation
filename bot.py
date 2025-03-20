import time
import groupdocs_translation_cloud
from groupdocs_translation_cloud import TextRequest, PdfFileRequest

api = groupdocs_translation_cloud.api.TranslationApi()
file_api = groupdocs_translation_cloud.api.FileApi()
api.api_client.configuration.client_id = "a0ab8978-a4d6-412d-b9cd-fbfcea706dee"
api.api_client.configuration.client_secret = "310ccbd37a74f255fcfce47eae846f1b"

text_request = TextRequest(
    source_language="en", 
    target_languages=["es", "fr", "ar"], 
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
                print(lang + ": " + status_response.translations[lang][0])
                break
        time.sleep(2)
