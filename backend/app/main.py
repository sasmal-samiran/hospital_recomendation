import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import (
    hospitals_router,
    routes_router,
    weather_router,
    road_condition_router,
    recommendations_router,
    auth_router,
    history_router,
    admin_router
)
from app.services.road_model_service import road_model_service

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """FastAPI Application factory with routers, middleware, and structured error handlers."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Register Global Structured Error Handlers (no developer leaks, frontend ready)
    register_exception_handlers(app)

    # Enable CORS for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API v1 Routers
    api_prefix = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(hospitals_router, prefix=api_prefix)
    app.include_router(routes_router, prefix=api_prefix)
    app.include_router(weather_router, prefix=api_prefix)
    app.include_router(road_condition_router, prefix=api_prefix)
    app.include_router(recommendations_router, prefix=api_prefix)
    app.include_router(history_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

    # @app.on_event("startup")
    # async def startup_event():
    #     """Preload CLIP vision model in a background thread without blocking server boot."""
    #     import threading
    #     logger.info("Server started. Preloading CLIP vision model in background...")
    #     threading.Thread(target=road_model_service.load_model, daemon=True).start()

    @app.get("/", tags=["General"], summary="API Root / Overview")
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "endpoints": {
                "auth": f"{api_prefix}/auth/login",
                "hospitals": f"{api_prefix}/hospitals/nearby",
                "routes": f"{api_prefix}/routes/calculate",
                "weather": f"{api_prefix}/weather/current",
                "road_condition": f"{api_prefix}/road-condition/analyze-url",
                "recommendations": f"{api_prefix}/recommendations/best-hospitals",
                "history": f"{api_prefix}/history/my-history",
                "admin": f"{api_prefix}/admin/stats"
            }
        }

    @app.get("/health", tags=["General"], summary="Health Check")
    def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app

app = create_app()
