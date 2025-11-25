FROM python:3.11-alpine

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev mariadb-connector-c-dev tzdata pkgconfig \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} app:app"]
