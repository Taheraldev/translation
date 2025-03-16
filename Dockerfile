FROM python:3.9

COPY requirements.txt /app/
WORKDIR /app

# ترقية pip أولاً
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app/
CMD ["python3", "bot.py"]
