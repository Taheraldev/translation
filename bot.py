import requests

url = "https://api.groupdocs.cloud/v2.0/translation/pdf"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}
files = {
    "file": open("your_file.pdf", "rb")
}
data = {
    "sourceLanguage": "en",
    "targetLanguages": ["ar"],
    "outputFormat": "pdf"
}

response = requests.post(url, headers=headers, files=files, json=data)

if response.status_code == 200:
    print("✅ تم الترجمة بنجاح!")
else:
    print("❌ خطأ أثناء الترجمة:", response.text)
