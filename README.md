# PulseRoute AI - Weather & Traffic-Aware Hospital Recommendation System

An intelligent Emergency Hospital Route Finding and Ranking System that calculates optimal driving routes to nearby hospitals by integrating:
- **Real-Time Driving Duration & Traffic Congestion** (Google Routes & Places API)
- **Road Surface Conditions & Vision Quality Scores (0-100)** (CLIP Zero-Shot Vision AI)
- **Real-Time Weather Hazards & Safety Penalty Index** (OpenWeatherMap API)
- **Composite Emergency Suitability Scoring & Ranking**
- **JWT Authentication, User Profiles, Search History & Admin Management Console**
- **Modern, Responsive Frontend Service (HTML5, Vanilla CSS, Vanilla JavaScript, Leaflet.js Maps)**

---

## Architecture & Project Structure

```
hospitalFinding/
├── app/                           # Backend FastAPI Service (Port 8000)
│   ├── core/
│   │   ├── config.py              # Configuration & Environment Variables
│   │   ├── security.py            # JWT Token Creation/Verification & Bcrypt Hashing
│   │   └── exceptions.py          # Structured Error Handlers (Zero-Fallback Policy)
│   ├── db/
│   │   └── database.py            # SQLite database with Auto-Seeded Demo Accounts
│   ├── schemas/                   # Pydantic Schemas
│   │   ├── auth.py
│   │   ├── hospital.py
│   │   ├── route.py
│   │   ├── weather.py
│   │   ├── road_condition.py
│   │   ├── recommendation.py
│   │   ├── history.py
│   │   └── admin.py
│   ├── services/                  # Business Logic Layer
│   │   ├── places_service.py      # Google Places API integration
│   │   ├── routes_service.py      # Google Routes API & Polyline decoding
│   │   ├── weather_service.py     # OpenWeatherMap API & hazard penalties
│   │   ├── road_model_service.py  # CLIP Vision classification
│   │   └── scoring_service.py     # Multi-factor ranking algorithm
│   ├── routers/                   # REST API Controllers
│   │   ├── auth.py                # /api/v1/auth/*
│   │   ├── hospitals.py           # /api/v1/hospitals/*
│   │   ├── routes.py              # /api/v1/routes/*
│   │   ├── weather.py             # /api/v1/weather/*
│   │   ├── road_condition.py      # /api/v1/road-condition/*
│   │   ├── recommendations.py     # /api/v1/recommendations/*
│   │   ├── history.py             # /api/v1/history/*
│   │   └── admin.py               # /api/v1/admin/*
│   └── main.py                    # App Factory & CORS Middleware
├── frontend/                      # Separate Frontend Service (Port 3000)
│   ├── css/
│   │   └── styles.css             # Modern Healthcare UI Design System (Vanilla CSS)
│   ├── js/
│   │   ├── config.js              # API Base URL & Runtime Environment Settings
│   │   ├── api.js                 # Central API Client with JWT Header Injection
│   │   ├── auth.js                # Auth State & Session Management
│   │   ├── map.js                 # Leaflet.js Interactive Routing Map Controller
│   │   ├── router.js              # Client-Side Hash Router with Role Guards
│   │   └── app.js                 # Main Controller & UI Event Handlers
│   ├── index.html                 # Complete Single Page Application
│   └── serve.py                   # Standalone Python Static Server
├── test/                          # Preserved Legacy Scripts
├── main.py                        # Backend Uvicorn Runner
├── requirements.txt
└── README.md
```

---

## Demo Accounts

The database is pre-seeded with accounts for instant login:

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **Admin** | `admin@emergency.com` | `Admin@123` | Full Admin Console, Metrics, User Role Manager, Query Logs |
| **User** | `user@emergency.com` | `User@123` | Emergency Finder, Dashboard, Search History, Medical Profile |

---

## Quick Start Guide

### Step 1: Start the Backend API Service (Port 8000)
```powershell
python main.py
```
*Backend runs on **http://localhost:8000***  
*Interactive Swagger Documentation: **http://localhost:8000/docs***

### Step 2: Start the Frontend Service (Port 3000)
In a separate terminal:
```powershell
cd frontend
python serve.py
```
*Open **http://localhost:3000** in your browser to access the complete application.*

---

## Frontend Pages & Features

1. **Landing / Home (`#landing`)**: Hero showcase with system overview, features, and direct emergency call to action.
2. **Emergency Recommendation (`#emergency`)**:
   - Live GPS Geolocation button (`navigator.geolocation`)
   - Adjustable Search Radius slider (1 km – 15 km)
   - Optional Road Surface Vision AI: public image URL or local photo upload
   - Interactive Leaflet.js Map with color-coded traffic polyline routes and custom hospital badges
   - Top #1 Recommended Hospital Hero card with multi-criteria score progress breakdown
   - Alternative candidate hospitals list sorted by composite score
3. **Hospital Details (`#hospital-detail`)**:
   - Turn-by-turn distance and travel time
   - Congestion ratio and traffic status
   - Live weather hazards and road condition assessment
   - Direct Google Maps navigation link
4. **Sign In (`#login`) & Sign Up (`#register`)**:
   - Form validation, instant token storage in localStorage, demo account quick links
5. **User Dashboard (`#dashboard`)**:
   - Medical profile summary (blood group, emergency contact)
   - Live local weather widget
   - Recent search query shortcuts
6. **User Profile (`#profile`)**:
   - Edit full name, blood group, emergency contact, phone number
   - Secure password update
7. **Search History (`#history`)**:
   - Comprehensive table of past queries
   - One-click historical route reload onto the interactive map
   - Delete history records
8. **Admin Dashboard (`#admin`)**:
   - Live system metrics (Total Users, Admins, Emergency Queries, Avg ETA)
   - User Management Table (Promote/Demote user roles)
   - Real-time emergency query logs with coordinates and timestamps
9. **Error Screens**:
   - `401 Unauthorized`
   - `403 Forbidden` (Non-admin access restriction)
   - `404 Page Not Found`
   - `500 Server Error`

---

## API Endpoints Reference

### Authentication & Profile (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Register a new account
- `POST /api/v1/auth/login` — Sign in and obtain JWT Bearer token
- `GET /api/v1/auth/me` — Protected: Get current user profile
- `PUT /api/v1/auth/profile` — Protected: Update user medical details
- `POST /api/v1/auth/change-password` — Protected: Update password

### Recommendation History (`/api/v1/history`)
- `GET /api/v1/history/my-history` — Protected: Fetch user recommendation records
- `POST /api/v1/history/save` — Protected: Save recommendation result
- `GET /api/v1/history/{history_id}` — Protected: Get specific record detail
- `DELETE /api/v1/history/{history_id}` — Protected: Delete record

### Admin Management (`/api/v1/admin`)
- `GET /api/v1/admin/stats` — Admin Only: System metrics & summary
- `GET /api/v1/admin/users` — Admin Only: List all registered accounts
- `PUT /api/v1/admin/users/{user_id}/role` — Admin Only: Update role (`user` / `admin`)
- `GET /api/v1/admin/logs` — Admin Only: System-wide emergency query stream

### Emergency Routing & Services (`/api/v1/`)
- `POST /api/v1/recommendations/best-hospitals` — Multi-factor emergency routing & ranking
- `GET /api/v1/hospitals/nearby` — Nearby hospitals search
- `POST /api/v1/routes/calculate` — Google Routes directions and congestion
- `GET /api/v1/weather/current` — Live OpenWeather parameters and safety score
- `POST /api/v1/weather/along-route` — Weather sampled along route polyline
- `POST /api/v1/road-condition/analyze-url` — CLIP AI zero-shot road scoring from URL
- `POST /api/v1/road-condition/analyze-upload` — CLIP AI road scoring from file upload
