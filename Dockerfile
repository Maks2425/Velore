FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build-time only values so `collectstatic` can run without a real .env file.
# Override DJANGO_SECRET_KEY (and everything else in .env.example) with real
# values at deploy time — these defaults are not secret and must not be relied on.
ENV DJANGO_SECRET_KEY=build-time-placeholder-override-in-deployment \
    DJANGO_DEBUG=False
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn velore.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
