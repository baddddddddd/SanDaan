FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV WEB_CONCURRENCY=2

ENV FLASK_APP=api

EXPOSE 5000

CMD ["gunicorn", "api:app", "--log-level", "debug"]
    