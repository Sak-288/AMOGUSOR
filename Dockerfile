# 1. Use an appropriate base image
# We are using a minimal image based on Debian's Bookworm, which supports Python 3.13.
FROM python:3.13-slim-bookworm

# 2. Set environment variables
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# 3. Install System Dependencies (THE FIX IS HERE)
# We need libpq-dev for PostgreSQL, and libgl1 (or libgl1-mesa-glx) for OpenCV (cv2).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Dependencies for PostgreSQL (libpq-dev)
        libpq-dev \
        # Dependencies for OpenCV (libGL.so.1)
        libgl1 \
        # Clean up to keep image size small
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . /app/

# 6. Define the final deployment command
# This matches the run command from your original build log.
CMD python manage.py migrate --noinput && gunicorn mysite.wsgi:application -b 0.0.0.0:$PORT