FROM python:3.10-slim

WORKDIR /app

# Copy requirements files
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY server.py .
COPY sf_connection.py .
COPY tools/ ./tools/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the server
CMD ["python", "server.py"]