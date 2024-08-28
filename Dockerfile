FROM python:3.12-slim

# Set environment variable to prevent writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy requirements file
COPY README.md pyproject.toml requirements.lock .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.lock

# Copy the app code and .env file
COPY ./src ./src

# Add this line to make the src directory a Python package
RUN touch ./src/__init__.py

COPY .env .

# Expose the app's port
EXPOSE 8000

# Update the CMD to use the correct module path
CMD ["python", "-m", "uvicorn", "src.fastapi_aiograpi.main:app", "--host", "0.0.0.0", "--port", "8000"]
