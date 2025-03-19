FROM python:3.9


WORKDIR /app

# نسخ الملفات المطلوبة
COPY requirements.txt .
COPY bot.py .

# ترقية pip أولاً
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app/
# تشغيل البوت
CMD ["python3", "bot.py"]
