# Use a Python image that's less likely to have C library issues
# 'slim' images are often better than 'alpine' for C extensions
FROM python:3.11-slim

# Install libpq, the PostgreSQL client library
# Note: On Debian-based images ('-slim' is Debian), this is 'libpq-dev'
#       But since we're using the binary wheel, we only need the runtime library.
#       Let's install both to be safe, but libpq5 is the runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Create a non-root user for security (optional but recommended)
RUN adduser --system --no-create-home appuser
USER appuser

# Run the script
CMD ["python", "vacancy_searcher_3000.py"]