# MBM Book Python Kernel - Full Data Science & ML Stack
# Includes: Python 3.11 + ALL major libraries (like Google Colab / Jupyter)

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies for scientific/ML/image libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ gfortran make cmake \
    libffi-dev libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 \
    libhdf5-dev liblapack-dev libblas-dev \
    libxml2-dev libxslt1-dev \
    libcairo2-dev pkg-config \
    git curl wget unzip \
    ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# ── Core Scientific Stack ──
RUN pip install --no-cache-dir \
    numpy pandas matplotlib seaborn plotly \
    scipy sympy statsmodels \
    ipython

# ── Machine Learning ──
RUN pip install --no-cache-dir \
    scikit-learn scikit-image \
    xgboost lightgbm catboost \
    imbalanced-learn

# ── TensorFlow (CPU) ──
RUN pip install --no-cache-dir tensorflow

# ── PyTorch (CPU) ──
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# ── Image Processing ──
RUN pip install --no-cache-dir \
    opencv-python-headless pillow \
    imageio mahotas

# ── NLP ──
RUN pip install --no-cache-dir \
    nltk spacy transformers \
    datasets tokenizers sentencepiece \
    gensim

# ── Deep Learning Extras ──
RUN pip install --no-cache-dir \
    keras h5py \
    onnx onnxruntime

# ── Data Handling & Visualization ──
RUN pip install --no-cache-dir \
    openpyxl xlsxwriter xlrd \
    bokeh altair \
    networkx pydot graphviz \
    tabulate prettytable \
    tqdm rich

# ── Web & API ──
RUN pip install --no-cache-dir \
    requests httpx aiohttp \
    beautifulsoup4 lxml \
    flask fastapi uvicorn \
    scrapy selenium

# ── Databases ──
RUN pip install --no-cache-dir \
    sqlalchemy pymongo redis \
    sqlite-utils

# ── Utilities ──
RUN pip install --no-cache-dir \
    pyyaml toml pydantic \
    python-dotenv click typer \
    Cython numba \
    joblib dill cloudpickle \
    regex faker

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')" 2>/dev/null || true

WORKDIR /workspace
CMD ["python"]
