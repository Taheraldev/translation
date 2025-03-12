FROM python:3.9-slim

# تثبيت التبعيات النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    pdf2htmlEX \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
