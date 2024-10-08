FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.lock

# Ensure Sentry and other dependencies are installed
RUN pip install --no-cache-dir psycopg2-binary

EXPOSE 5569

CMD ["python", "-m", "uvicorn", "src.fastapi_aiograpi.main:app", "--host", "0.0.0.0", "--port", "5569"]
