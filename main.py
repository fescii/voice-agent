"""
FastAPI AI Voice Agent System
Main application entry point
"""
import uvicorn
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.v1 import router as api_v1_router
from core.config.appconfig.main import AppConfig
from core.logging.setup import setup_logging
from core.startup.manager import StartupManager
from core.startup.context import get_startup_context
from wss.endpoint import websocket_router


# Initialize startup manager globally to maintain context throughout app lifecycle
startup_manager = StartupManager()


# Startup context is now imported from core.startup.context


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Application lifespan manager to handle startup and shutdown events."""
  async with startup_manager.startup_context() as context:
    # Store startup context in app state
    app.state.startup_context = context
    yield
  # Cleanup happens automatically in the startup_context context manager


def create_app() -> FastAPI:
  """Create and configure the FastAPI application"""

  # Setup logging
  setup_logging()

  # Load app configuration
  config = AppConfig()

  # Create FastAPI app with lifespan context manager
  app = FastAPI(
      title=config.app_name,
      version=config.version,
      debug=config.debug_mode,
      description="AI Voice Agent System with Ringover Integration",
      lifespan=lifespan
  )

  # Add CORS middleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # Configure appropriately for production
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Define system health endpoint
  @app.get("/health", status_code=status.HTTP_200_OK)
  async def health_check(context=Depends(get_startup_context)):
    """System health check endpoint."""
    healthy = context.is_healthy()

    if not healthy:
      failed_services = context.get_failed_services()
      raise HTTPException(
          status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
          detail=f"Services unavailable: {failed_services}"
      )

    return {
        "status": "healthy",
        "services": {
            name: service.status for name, service in context.services.items()
        },
        "startup_time": context.startup_time.isoformat(),
        "uptime_seconds": (asyncio.get_event_loop().time() -
                           context.startup_time.timestamp())
    }

  # Include routers
  app.include_router(api_v1_router, prefix="/api/v1")
  app.include_router(websocket_router, prefix="/ws")

  return app


app = create_app()

if __name__ == "__main__":
  config = AppConfig()
  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=getattr(config, "server_port", 8000),
      reload=config.debug_mode,
      log_level="info"
  )
