FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system packages and playwright deps
RUN apt-get update && apt-get install -y wget gnupg && \
    pip install --upgrade pip && \
    pip install playwright && \
    playwright install-deps && \
    playwright install

# Copy dependency file and install app requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
ENV PYTHONPATH=/app

# Expose port
EXPOSE 10000

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
