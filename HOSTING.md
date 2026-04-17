# MBM Book — Hosting Guide

## Quick Start (Single PC)

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+** installed (LTS recommended)

### 1. Install Backend Dependencies
```powershell
cd D:\Mbmbook
python -m pip install fastapi "uvicorn[standard]" websockets sqlalchemy aiosqlite pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart psutil GPUtil httpx aiofiles orjson email-validator
```

### 2. Install Frontend Dependencies
```powershell
cd D:\Mbmbook\frontend
npm install
```

### 3. Configure `.env`
Create or edit `.env` in the project root (`D:\Mbmbook\.env`):
```env
MBM_DEBUG=true
MBM_HOST=0.0.0.0
MBM_PORT=8000
MBM_HOST_IP=<YOUR_PC_IP>
MBM_ALLOWED_SUBNET=10.10.12.0/23
MBM_SECRET_KEY=mbmbook-dev-key-change-in-production
MBM_DATABASE_URL=sqlite+aiosqlite:///data/mbmbook.db
```
Replace `<YOUR_PC_IP>` with the hosting PC's LAN IP (e.g. `10.10.13.242`).

To find your IP:
```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "10.10.*" }).IPAddress
```

### 4. Update Frontend Proxy
Edit `frontend/vite.config.ts` and set the proxy target to your IP:
```ts
target: 'http://<YOUR_PC_IP>:8000'
```

### 5. Create Data Directory
```powershell
mkdir D:\Mbmbook\data -ErrorAction SilentlyContinue
```

### 6. Start Backend
```powershell
cd D:\Mbmbook
python -m backend.server
```
Backend runs at `http://<YOUR_PC_IP>:8000`

### 7. Start Frontend (new terminal)
```powershell
cd D:\Mbmbook\frontend
npm run dev
```
Frontend runs at `http://<YOUR_PC_IP>:3000`

---

## Hosting on Another Lab PC (CLI)

Copy the entire `D:\Mbmbook` folder to the other PC, then run:

```powershell
# 1. Get this PC's LAN IP
$MY_IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "10.10.*" }).IPAddress
Write-Host "This PC's IP: $MY_IP"

# 2. Install Python deps
cd D:\Mbmbook
python -m pip install fastapi "uvicorn[standard]" websockets sqlalchemy aiosqlite pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart psutil GPUtil httpx aiofiles orjson email-validator

# 3. Install frontend deps
cd D:\Mbmbook\frontend
npm install

# 4. Update .env with this PC's IP
cd D:\Mbmbook
(Get-Content .env) -replace 'MBM_HOST_IP=.*', "MBM_HOST_IP=$MY_IP" | Set-Content .env

# 5. Create data dir
mkdir D:\Mbmbook\data -ErrorAction SilentlyContinue

# 6. Start backend (Terminal 1)
cd D:\Mbmbook
python -m backend.server

# 7. Start frontend (Terminal 2)
cd D:\Mbmbook\frontend
npm run dev
```

### Windows Firewall Rules (run as Administrator)
```powershell
New-NetFirewallRule -DisplayName "MBM Book Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
New-NetFirewallRule -DisplayName "MBM Book Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
```

---

## Access

- **Frontend**: `http://<HOST_PC_IP>:3000` from any device on the college LAN
- **API Docs**: `http://<HOST_PC_IP>:8000/docs` (Swagger UI)
- **Health Check**: `http://<HOST_PC_IP>:8000/health`

Only devices on the `10.10.12.0/23` subnet (college WiFi) can access MBM Book. Others get a 403 Forbidden response.
