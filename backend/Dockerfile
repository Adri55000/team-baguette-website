FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1

WORKDIR /app

COPY requirements.txt requirements.lock.txt ./

RUN pip install --no-cache-dir -r requirements.lock.txt

COPY app/ ./app/
COPY resources/ ./resources/
COPY migrations/ ./migrations/
COPY alembic.ini ./alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
