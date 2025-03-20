import groupdocs_translation_cloud
from groupdocs_translation_cloud.models.pdf_file_request import PdfFileRequest
from groupdocs_translation_cloud.models.status_response import StatusResponse
from groupdocs_translation_cloud.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.groupdocs.cloud/v2.0/translation
# See configuration.py for a list of all supported configuration parameters.
configuration = groupdocs_translation_cloud.Configuration(
    host = "https://api.groupdocs.cloud/v2.0/translation"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with groupdocs_translation_cloud.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = groupdocs_translation_cloud.TranslationApi(api_client)
    pdf_file_request = groupdocs_translation_cloud.PdfFileRequest() # PdfFileRequest | String in body of request, containing JSON with parameters for translation. (optional)

    try:
        # Trial pdf translation. Translate only first page without conversion to another format.
        api_response = api_instance.pdf_trial_post(pdf_file_request=pdf_file_request)
        print("The response of TranslationApi->pdf_trial_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TranslationApi->pdf_trial_post: %s\n" % e)
