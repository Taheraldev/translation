import requests

# إعدادات API
API_URL = "https://openl-translate.p.rapidapi.com/translate/bulk"
HEADERS = {
    "X-RapidAPI-Key": "7b73717e2dmshbd139747c640560p175307jsn75624bf31396",
    "X-RapidAPI-Host": "openl-translate.p.rapidapi.com",
    "Content-Type": "application/json"
}

# بيانات الترجمة
data = {
    "text": ["Hello, world!"],
    "source_lang": "en",
    "target_lang": "ar"
}

response = requests.post(API_URL, json=data, headers=HEADERS)

if response.status_code == 200:
    print("✅ استجابة ناجحة:", response.json())
else:
    print(f"❌ فشل الترجمة: {response.status_code}, {response.text}")
