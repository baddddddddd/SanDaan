FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV WEB_CONCURRENCY=2

ENV FLASK_APP=api

EXPOSE 5000

CMD ["gunicorn", "api:app", "-b", "0.0.0.0:5000", "--log-level", "debug", "--timeout", "600"]
