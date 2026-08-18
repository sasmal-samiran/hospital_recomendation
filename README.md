# PulseRoute AI - Hospital Recommendation System

A weather, traffic, and road-quality aware emergency hospital route recommendation engine.

---

## Project Structure

```
hospitalFinding/
├── docker-compose.yml       # Connects backend and frontend with live development bind mounts
├── .env.example             # Environment variables template
├── .dockerignore            # Root Docker exclusion rules
├── backend/                 # Backend service (FastAPI)
│   ├── app/                 # Application code (AI model, scoring, routes, auth)
│   ├── main.py              # Application entrypoint
│   ├── requirements.txt     # Backend-only dependencies
│   ├── Dockerfile           # Backend container definition
│   └── .dockerignore        # Backend build exclusions
└── frontend/                # Frontend service (HTML5, CSS3, JS, Leaflet.js, Nginx)
    ├── index.html           # Single Page Application
    ├── css/                 # CSS stylesheet
    ├── js/                  # Client logic and mapping
    ├── nginx.conf           # Nginx SPA and reverse-proxy config
    ├── Dockerfile           # Frontend container definition
    └── .dockerignore        # Frontend build exclusions
```

---

## Quick Start with Docker Compose

### 1. Clone the repository
```bash
git clone <repository-url>
cd hospitalFinding
```

### 2. Create `.env` file
Copy the template configuration:
```bash
# On Linux / macOS / PowerShell:
cp .env.example .env
```
*(Optionally provide your own Google Maps or OpenWeather API keys in `.env`)*

### 3. Start all services
```bash
docker compose up
```
*(To run in background / detached mode, use `docker compose up -d`)*

Once started, open:
* **Frontend Web App**: [http://localhost:3000](http://localhost:3000)
* **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Stop all services
```bash
docker compose down
```

---

## Development Workflow

### Live Code Changes (No Rebuild Needed)
Both services use **volume bind mounts**:
* **Backend**: Changes made to Python files in `backend/` are **automatically reloaded** by Uvicorn in real-time.
* **Frontend**: Changes made to HTML, CSS, or JS files in `frontend/` **reflect immediately** upon browser refresh.

### Rebuilding After Dependency Changes
If you add or update packages in `backend/requirements.txt` or modify Dockerfiles, rebuild the images with:
```bash
docker compose up --build
```
Or rebuild specific services:
```bash
docker compose build backend
docker compose build frontend
```

---

## Independent Service Development

### Working on the Backend Only (No Frontend Dependencies Needed)
Run only the backend container:
```bash
docker compose up backend
```
Or run natively on your machine:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Working on the Frontend Only (No Backend Dependencies Needed)
Run only the frontend container:
```bash
docker compose up frontend
```
Or run natively using Python's built-in static server:
```bash
cd frontend
python serve.py
```

---

## Demo Accounts

The local database auto-seeds the following accounts on first boot:

| Role | Email | Password | Access |
|---|---|---|---|
| **Admin** | `admin@emergency.com` | `Admin@123` | Full admin metrics, logs, role control |
| **User** | `user@emergency.com` | `User@123` | Emergency route finding, history, profile |
