FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        libmariadb-dev-compat \
        pkg-config \
        libpq-dev \
        build-essential

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY . .

EXPOSE 8000

CMD ["gunicorn", "delivery_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "8"]
