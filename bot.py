import requests

# بيانات المصادقة
client_id = "a91a6ad1-7637-4e65-b793-41af55450807"
client_secret = "2d0c949f2cc2d12010f5427e6c1dc4da"

# رابط طلب التوكن
url = "https://api.groupdocs.cloud/connect/token"

# بيانات الطلب
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# إرسال الطلب وجلب التوكن
response = requests.post(url, data=data)

# إذا كان الطلب ناجحًا، اطبع التوكن
if response.status_code == 200:
    access_token = response.json().get("access_token")
    print("🔑 ACCESS_TOKEN:", access_token)
else:
    print("❌ فشل في الحصول على التوكن:", response.text)
