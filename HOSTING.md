# MBM Book — Hosting Guide

## One-Click Setup (Recommended)

### Prerequisites
- **Docker Desktop** installed ([download](https://docker.com/products/docker-desktop))

### Steps
1. Clone the repository:
   ```powershell
   git clone https://github.com/RamMAC17/Mbmbook.git
   cd Mbmbook
   ```
2. Double-click **`start.bat`**
3. Wait for the build to complete (first time takes ~15-30 min for Python ML libraries)
4. MBM Book opens in your browser at `http://localhost:9999`

That's it! The batch file handles everything:
- Starts Docker Desktop if not running
- Builds the Python kernel with 80+ libraries (TensorFlow, PyTorch, OpenCV, etc.)
- Builds and starts the application via Docker Compose
- Opens your browser automatically

### Python Libraries Included
The Python kernel comes pre-loaded with all major data science and ML libraries:

| Category | Libraries |
|----------|-----------|
| **Core** | numpy, pandas, matplotlib, seaborn, plotly, scipy, sympy, statsmodels |
| **Machine Learning** | scikit-learn, xgboost, lightgbm, catboost, imbalanced-learn |
| **Deep Learning** | tensorflow, torch, torchvision, keras, transformers |
| **Image Processing** | opencv, pillow, scikit-image, imageio |
| **NLP** | nltk, spacy, transformers, gensim, tokenizers |
| **Data** | openpyxl, sqlalchemy, h5py, beautifulsoup4, lxml |
| **Visualization** | plotly, bokeh, altair, networkx |
| **Utilities** | requests, httpx, tqdm, rich, pyyaml, faker |

### Stopping
Press any key in the batch file terminal, or run:
```powershell
cd path\to\Mbmbook
docker compose down
```

---

## Manual Setup (Without Docker Compose)

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** installed (LTS recommended)
- **Docker Desktop** installed (for kernel isolation)

### 1. Install Backend Dependencies
```powershell
cd D:\Mbmbook
python -m pip install fastapi "uvicorn[standard]" websockets sqlalchemy aiosqlite pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart psutil GPUtil httpx aiofiles orjson email-validator
```

### 2. Install Frontend Dependencies & Build
```powershell
cd D:\Mbmbook\frontend
npm install
npm run build
```

### 3. Build Python Kernel Image
```powershell
docker build -t mbmbook-kernel-python -f kernels\docker\python\Dockerfile kernels\docker\python\
```

### 4. Configure `.env`
Create `.env` in the project root:
```env
MBM_DEBUG=true
MBM_HOST=0.0.0.0
MBM_PORT=9999
MBM_HOST_IP=<YOUR_PC_IP>
MBM_DATABASE_URL=sqlite+aiosqlite:///data/mbmbook.db
```

### 5. Start Backend
```powershell
cd D:\Mbmbook
python -m backend.server
```
Access at `http://<YOUR_PC_IP>:9999`

---

## Windows Firewall (if needed)
Run as Administrator:
```powershell
New-NetFirewallRule -DisplayName "MBM Book" -Direction Inbound -Protocol TCP -LocalPort 9999 -Action Allow
```

---

## Access

- **App**: `http://<HOST_PC_IP>:9999` from any device on the LAN
- **API Docs**: `http://<HOST_PC_IP>:9999/docs` (Swagger UI)
- **Health Check**: `http://<HOST_PC_IP>:9999/health`
