# Load the gem
import groupdocs_translation_cloud
# Get Client Id and Client Secret from https://dashboard.groupdocs.cloud
my_client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
my_client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# Create instance of the API
configuration = Configuration(apiKey=my_client_secret, appSid=my_client_id)
api = TranslationApi(configuration)

#document translation
pair = "en-fr"
_format = "docx"
storage = "First Storage"
name = "test.docx"
folder = ""
savepath = ""
savefile = "test_python.docx"  
masters = False
elements = []
translator = TranslateDocument(pair, _format, storage, name, folder, savepath, savefile, masters, elements)
request = translator.to_string()
res_doc = api.post_translate_document(request)
print(res_doc.message)
