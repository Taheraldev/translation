import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.pdf_file_request import PdfFileRequest
from groupdocs_translation_cloud.rest import ApiException
from pprint import pprint
import os

# Configure access token
configuration = groupdocs_translation_cloud.Configuration(
    host="https://api.groupdocs.cloud/v2.0/translation"
)
configuration.access_token = os.environ["ACCESS_TOKEN"]

# Create API client
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)
    
    # Manually construct the request payload
    pdf_file_request = PdfFileRequest(
        source_file={
            "file_path": "file.pdf"  # Specify your PDF file path
        },
        output_format="pdf",  # Required output format
        source_language="es",  # Source language code (e.g., Spanish)
        target_languages=["en"],  # List of target language codes (e.g., English)
    )
    
    try:
        # Execute the request
        api_response = api_instance.pdf_trial_post(pdf_file_request=pdf_file_request)
        print("Response from TranslationApi->pdf_trial_post:")
        pprint(api_response)
    except ApiException as e:
        print(f"Exception: {e}\n")
