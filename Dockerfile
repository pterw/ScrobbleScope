FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

# Single worker keeps JOBS dict in shared memory; 4 threads handle concurrent
# HTTP requests (progress polls, form submits) without breaking job state.
# Appropriate for shared-cpu-2x / 512MB on Fly.io (threads are I/O-bound).
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "app:app"]
