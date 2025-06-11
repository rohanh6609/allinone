FROM python:3.10
RUN pip install --upgrade pip
WORKDIR /app
COPY . .
RUN python -m pip install "pymongo[srv]"
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libc-dev \
    ffmpeg \
    aria2 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt
CMD ["python3", "main.py"]
