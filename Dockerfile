FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

WORKDIR /app

# mysqlclient is declared in requirements.txt, so keep the native build
# dependencies available during dependency installation only.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

EXPOSE 5000

# Keep the project's Flask development server, but bind it to all interfaces
# so the host can reach the container during local development.
CMD ["flask", "--app", "run", "run", "--host=0.0.0.0", "--port=5000", "--debug"]
