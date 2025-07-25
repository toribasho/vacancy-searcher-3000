# --- Stage 1: Build dependencies ---
FROM python:3.11-alpine AS builder

# Install build dependencies
# We need python3-dev and build-base to compile C extensions
RUN apk add --no-cache postgresql-dev python3-dev build-base

WORKDIR /app
COPY requirements.txt .

# Install dependencies, which will trigger the compilation of psycopg2
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final runtime image ---
FROM python:3.11-alpine AS final

# Only install runtime dependencies
RUN apk add --no-cache libpq

WORKDIR /app
# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY . /app

# Create a non-root user (optional but recommended)
RUN addgroup -S appuser && adduser -S appuser -G appuser
USER appuser

# Run the script
CMD ["python", "vacancy_searcher_3000.py"]