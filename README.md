# MBM Book

A distributed, multi-language notebook platform — like Google Colab meets Jupyter — with **live code execution**, **notebook persistence**, and **LAN hosting** across multiple PCs. No internet required.

![MBM Book](logo.png)

---

## Features

- **Colab-like UI** — Monaco code editor, markdown cells, real-time output
- **Multi-language** — Python, JavaScript, C/C++, Java, Go, Rust, and 20+ more
- **Auto-save** — Notebooks persist in browser localStorage (survives refresh)
- **Download as .ipynb** — Export notebooks in Jupyter-compatible format
- **Dark / Mix / Light themes** — Full theme support with animated UI
- **Docker isolation** — Sandboxed code execution (optional, falls back to subprocess)
- **LAN hosting** — Host on any PC, access from others via ethernet — no WiFi needed

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Monaco Editor, Tailwind CSS, Zustand |
| Backend | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, aiosqlite |
| Execution | Docker containers (preferred) or direct subprocess |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Communication | WebSocket (live code output) |

---

## Quick Start — Host on Any PC

### Prerequisites

- **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Docker Desktop** (optional) — [docker.com](https://www.docker.com/products/docker-desktop/) — for sandboxed execution
- **Git** — [git-scm.com](https://git-scm.com/)

### 1. Clone the repo

```bash
git clone https://github.com/RamMAC17/Mbmbook.git
cd Mbmbook
```

### 2. Find your PC's IP address

```powershell
# Windows (PowerShell)
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1).IPAddress
```

```bash
# Linux/Mac
hostname -I | awk '{print $1}'
```

Write down this IP (e.g. `192.168.1.10`). You'll need it below.

### 3. Configure environment

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` and set **your PC's IP**:

```env
MBM_DEBUG=true
MBM_HOST=0.0.0.0
MBM_PORT=8000
MBM_HOST_IP=YOUR_IP_HERE
MBM_ALLOWED_SUBNET=192.168.0.0/16,169.254.0.0/16,172.16.0.0/12,10.0.0.0/8
MBM_SECRET_KEY=mbmbook-dev-key-change-in-production
MBM_DATABASE_URL=sqlite+aiosqlite:///data/mbmbook.db
```

### 4. Update the frontend proxy

Edit `frontend/vite.config.ts` and replace the IP with **your PC's IP**:

```typescript
proxy: {
  '/api': {
    target: 'http://YOUR_IP_HERE:8000',
    changeOrigin: true,
  },
  '/ws': {
    target: 'ws://YOUR_IP_HERE:8000',
    ws: true,
  },
},
```

### 5. Install backend dependencies

```powershell
# Windows — open PowerShell in the project root
pip install fastapi uvicorn[standard] websockets sqlalchemy aiosqlite pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart psutil GPUtil httpx aiofiles orjson
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 7. Build Docker kernel (optional — for sandboxed execution)

```bash
docker build -t mbmbook-kernel-python kernels/docker/python/
```

> If Docker is not installed or not running, code runs directly via subprocess (still works fine).

### 8. Start the servers

**Terminal 1 — Backend:**
```powershell
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### 9. Open in browser

- **On the host PC:** http://localhost:3000
- **From other PCs on the network:** http://YOUR_IP_HERE:3000

---

## Host Across Multiple PCs (No WiFi / No Internet)

You can run MBM Book on a private network of 2–4+ PCs using just **ethernet cables** and an optional **switch**. No router, no WiFi, no internet needed.

### Hardware needed

| Setup | Hardware | Cost |
|-------|----------|------|
| 2 PCs | 1 ethernet cable | ~₹50 |
| 3-4 PCs | 1 ethernet switch (5-port) + cables | ~₹400-600 |

### Network setup

1. **Connect** all PCs to the switch (or directly for 2 PCs)
2. **Set static IPs** on each PC — Windows: `Settings → Network → Ethernet → IP settings → Manual`

| PC | Role | IP Address | Subnet Mask |
|----|------|-----------|-------------|
| PC1 | **Server (host)** | `192.168.1.1` | `255.255.255.0` |
| PC2 | Client | `192.168.1.2` | `255.255.255.0` |
| PC3 | Client | `192.168.1.3` | `255.255.255.0` |
| PC4 | Client | `192.168.1.4` | `255.255.255.0` |

3. **On PC1 (server)** — clone the repo, set `MBM_HOST_IP=192.168.1.1` in `.env`, update `vite.config.ts` proxy to `192.168.1.1`, then start both servers (steps 5-8 above)
4. **On all other PCs** — open browser and go to: **http://192.168.1.1:3000**

> **Security:** Only PCs physically connected to the switch/cable can access MBM Book. The `MBM_ALLOWED_SUBNET` config controls which IP ranges are permitted.

### Using APIPA (zero-config for 2 PCs)

If you connect two PCs with just an ethernet cable and **don't set static IPs**, Windows will auto-assign IPs in the `169.254.x.x` range (APIPA). MBM Book allows this range by default.

1. Connect the two PCs with an ethernet cable
2. Wait ~30 seconds for auto-IP assignment
3. Run `ipconfig` on each PC to find the assigned `169.254.x.x` address
4. Set that IP in `.env` and `vite.config.ts` on the server PC
5. Start MBM Book and access from the other PC

---

## Project Structure

```
Mbmbook/
├── backend/                # FastAPI backend
│   ├── api/                # REST + WebSocket endpoints
│   │   ├── notebooks.py    # Notebook CRUD API
│   │   └── ws.py           # WebSocket handler (code execution)
│   ├── core/               # Config, security, database
│   │   └── config.py       # Settings (env-based)
│   └── services/           # Business logic
│       ├── kernel_manager.py   # Docker/subprocess execution
│       └── kernel_registry.py  # Language definitions (25+)
├── frontend/               # React frontend
│   ├── public/             # Static assets (logo.png)
│   └── src/
│       ├── components/     # UI components (Notebook, Cells, Toolbar, Sidebar)
│       ├── services/       # WebSocket client
│       └── stores/         # Zustand state (notebook, theme)
├── kernels/                # Kernel definitions
│   └── docker/python/      # Python kernel Dockerfile
├── data/                   # Runtime data (SQLite DB)
├── .env.example            # Environment template
├── docker-compose.yml      # Docker services
└── pyproject.toml          # Python project config
```

---

## Supported Languages

Python, JavaScript, TypeScript, C, C++, Java, Go, Rust, C#, Ruby, PHP, R, Julia, Scala, Kotlin, Swift, Perl, Haskell, Lua, Bash, SQL, and more.

> Language support depends on having the compiler/interpreter installed on the host PC (subprocess mode) or the Docker kernel image built.

---

## Configuration

All settings use the `MBM_` prefix and can be set in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MBM_HOST` | `0.0.0.0` | Bind address |
| `MBM_PORT` | `8000` | Backend port |
| `MBM_HOST_IP` | `10.10.13.242` | Your PC's LAN IP |
| `MBM_ALLOWED_SUBNET` | `192.168.0.0/16,...` | Comma-separated allowed subnets |
| `MBM_DATABASE_URL` | `sqlite+aiosqlite:///data/mbmbook.db` | Database connection |
| `MBM_KERNEL_TIMEOUT` | `3600` | Max execution time (seconds) |
| `MBM_MAX_KERNELS_PER_NODE` | `10` | Max concurrent kernels |

---

## License

MBM
