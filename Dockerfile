FROM python:3.12-slim

ENV REDIS_HOST=redis
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

EXPOSE 5569

CMD ["python", "-m", "uvicorn", "src.fastapi_aiograpi.main:app", "--host", "0.0.0.0", "--port", "5569"]
