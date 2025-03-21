FROM python:3.9-slim

# تثبيت Tesseract والخطوط العربية
FROM python:3.9-slim

# تثبيت Tesseract والخطوط العربية
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-ara \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع (بما في ذلك الخطوط)
COPY . /app
WORKDIR /app

# نسخ الخط العربي إلى مجلد الخطوط

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]

# نسخ ملفات المشروع (بما في ذلك الخطوط)
COPY . /app
WORKDIR /app

# نسخ الخط العربي إلى مجلد الخطوط
COPY arial.ttf /usr/share/fonts/truetype/

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
