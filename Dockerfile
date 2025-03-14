FROM python:3.9-slim


# نسخ ملف requirements.txt وتثبيت المكتبات
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . /app/

# الأمر لتشغيل البوت
CMD ["python", "bot.py"]
