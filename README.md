# Taste Engine Monorepo

An AI-powered vector-search movie recommendation engine with PostgreSQL metadata database, Qdrant vector database, Redis cache, and MinIO object storage.

## Stack Overview
- **Frontend:** Next.js (App Router, Tailwind CSS, TypeScript, Framer Motion) managed via Bun
- **Backend:** FastAPI (Python 3.13) with database drivers configured for Python 3.13 compatibility
- **Database / Cache / Vector DB / Object Storage:** Local Docker Compose services

---

## 🚀 Running the Local Environment

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Bun (JavaScript/TypeScript runtime)

---

### Step 1: Spin up Infrastructure (Docker)
Ensure Docker is running. If you are on a system where Docker uses a specific socket path or Podman is active, specify `DOCKER_HOST` appropriately (e.g., `DOCKER_HOST=unix:///var/run/docker.sock`).

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker compose up -d
```

Verify services are healthy:
```bash
DOCKER_HOST=unix:///var/run/docker.sock docker compose ps
```

Services exposed:
- **PostgreSQL:** `localhost:5432`
- **Qdrant (Vector DB):** `localhost:6333`
- **Redis:** `localhost:6379`
- **MinIO S3 API:** `localhost:9000` (Web Dashboard: `http://localhost:9001` - `minioadmin/minioadmin`)

---

### Step 2: Start Backend (FastAPI)
Change to the `backend/` directory, activate the virtual environment, and run the FastAPI server:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend endpoints:
- **API Health:** `http://localhost:8000/health` (should return `{"status":"ok","database":"connected"}`)
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

### Step 3: Start Frontend (Next.js)
Change to the `frontend/` directory and run the Next.js development server using Bun:

```bash
cd frontend
bun run dev
```

Frontend endpoint:
- **Web App:** `http://localhost:3000`

---

## 🔧 Troubleshooting

### Database Driver compilation issues (Python 3.13)
The initial setup required database drivers updated to support Python 3.13:
- `asyncpg==0.31.0`
- `psycopg2-binary==2.9.12`

If you encounter issues re-installing, run:
```bash
./venv/bin/pip install -r requirements.txt
```
