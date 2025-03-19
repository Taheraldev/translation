# Dockerfile
FROM python:3.9-slim-buster

# تثبيت المتطلبات النظامية
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    fonts-noto \
    fonts-arabeyes \
    ttf-mscorefonts-installer \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# تحديث الفونت كاش
RUN fc-cache -f -v

# إنشاء مجلد العمل
WORKDIR /app

# نسخ الملفات المطلوبة
COPY requirements.txt .
COPY bot.py .

# ترقية pip أولاً
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# متغيرات البيئة
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Riyadh
COPY . /app/
# تشغيل البوت
CMD ["python3", "bot.py"]
