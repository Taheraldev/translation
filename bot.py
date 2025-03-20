import requests

# بيانات الاعتماد الخاصة بك
client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# عنوان endpoint لإنشاء access token
url = "https://api.groupdocs.cloud/connect/token"

# إعداد البيانات المطلوبة للطلب
payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# إرسال الطلب للحصول على token
response = requests.post(url, data=payload)
if response.status_code == 200:
    access_token = response.json().get("access_token")
    print("Access Token:", access_token)
else:
    print("فشل في إنشاء access token، رمز الحالة:", response.status_code)
