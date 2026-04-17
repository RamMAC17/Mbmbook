# MBM Book Python Kernel - Lightweight
# Includes: Python 3.11 + common data science packages

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal system deps for numpy/pandas wheel builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Python packages (lightweight set for fast builds)
RUN pip install --no-cache-dir \
    numpy pandas matplotlib scipy \
    requests

WORKDIR /workspace
CMD ["python"]
