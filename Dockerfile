FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python -m venv /app/venv

# Activate virtual environment and install dependencies
COPY requirements.txt .
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Set the virtual environment as the default Python environment
ENV PATH="/app/venv/bin:$PATH"

# Expose port
EXPOSE 8001

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
