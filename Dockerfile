FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ONLY bundled Chromium + OS dependencies
RUN playwright install chromium && playwright install-deps chromium

# Copy app code
COPY app/ ./app/

# Create data directory and give permissions to existing pwuser
RUN mkdir -p /app/data && chown -R pwuser:pwuser /app

# Use the pre-existing non-root user
USER pwuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]