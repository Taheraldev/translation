import requests

OPENL_API_KEY = '7b73717e2dmshbd139747c640560p175307jsn75624bf31396'
OPENL_TRANSLATE_ENDPOINT = 'https://api.openl.io/translate'

def test_translation():
    data = {
        'text': 'Hello, how are you?',
        'source_lang': 'en',
        'target_lang': 'ar'
    }
    headers = {'Authorization': f'Bearer {OPENL_API_KEY}'}
    
    response = requests.post(OPENL_TRANSLATE_ENDPOINT, json=data, headers=headers)
    
    if response.status_code == 200:
        print("✅ ترجمة ناجحة:", response.json().get('translated_text'))
    else:
        print(f"❌ فشل الترجمة: {response.status_code}, {response.text}")

test_translation()
