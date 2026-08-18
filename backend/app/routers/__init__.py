from app.routers.hospitals import router as hospitals_router
from app.routers.routes import router as routes_router
from app.routers.weather import router as weather_router
from app.routers.road_condition import router as road_condition_router
from app.routers.recommendations import router as recommendations_router
from app.routers.auth import router as auth_router
from app.routers.history import router as history_router
from app.routers.admin import router as admin_router

__all__ = [
    "hospitals_router",
    "routes_router",
    "weather_router",
    "road_condition_router",
    "recommendations_router",
    "auth_router",
    "history_router",
    "admin_router"
]
