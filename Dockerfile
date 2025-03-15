FROM python:3.9-slim
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . /app/
# الأمر لتشغيل البوت
CMD ["python", "bot.py"]
