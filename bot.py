ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE3NDIxOTY0ODIsImV4cCI6MTc0MjIwMDA4MiwiaXNzIjoiaHR0cHM6Ly9hcGkuZ3JvdXBkb2NzLmNsb3VkIiwiYXVkIjpbImh0dHBzOi8vYXBpLmdyb3VwZG9jcy5jbG91ZC9yZXNvdXJjZXMiLCJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl0sImNsaWVudF9pZCI6ImE5MWE2YWQxLTc2MzctNGU2NS1iNzkzLTQxYWY1NTQ1MDgwNyIsImNsaWVudF9kZWZhdWx0X3N0b3JhZ2UiOiJhNzA4ZTFhYS1hMjI1LTQxNjMtYWEwNS02YzE3MDU3NTUxMzQiLCJjbGllbnRfaWRlbnRpdHlfdXNlcl9pZCI6IjEwMjY4OTYiLCJzY29wZSI6WyJhcGkuYmlsbGluZyIsImFwaS5pZGVudGl0eSIsImFwaS5wcm9kdWN0cyIsImFwaS5zdG9yYWdlIl19.TiEtrBftDVwZWPugwZeX6A3Bsd8OcmlxduIVdJu-cWtu3R73DbKe39JeAh4gdYxPpVM5QbCmGUbXZL7XjDBmtRmY8q-V9f4XpBAH18cyv8NuNUyxvNPS1j17VK46IpP7rkv7WNOBpCb-BZbUZX4VPQlftGxmiiAxeT9Imq4_2I5egdbhkUCxqkki764jWlTSTDlGrgc5JR2SnUMAsGekxw7lXHXZgndeAPUmtV4BLi6zsGQC83BkkVsKIm1i9oG5H2aBa3j95giwj-YkWlxmlneKlkkxYn4ThiNvrPYNIQE7TPGwgFqWjDqr0nxJq4pf6TfYCAEjhkLIHg1oR4dxbg"  # ضع التوكن الحقيقي هنا

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
