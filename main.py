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
from core.config.registry import config_registry
from core.logging.setup import setup_logging
from core.startup.manager import StartupManager
from core.startup.context import get_startup_context
from core.startup.lifespan import lifespan_manager
from wss.endpoint import websocket_router


# Remove the old lifespan manager and use the new modular one


def create_app() -> FastAPI:
  """Create and configure the FastAPI application"""

  # Initialize centralized configuration registry
  config_registry.initialize()

  # Setup logging
  setup_logging()

  # Create FastAPI app with lifespan context manager
  app = FastAPI(
      title="AI Voice Agent System",
      version="1.0.0",
      debug=True,  # TODO: Get from centralized config
      description="AI Voice Agent System with Ringover Integration",
      lifespan=lifespan_manager
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
  uvicorn.run(
      "main:app",
      host="0.0.0.0",
      port=8001,  # Use different port to avoid conflicts
      reload=True,
      # Exclude logs and cache directories
      reload_dirs=[".", "!./logs", "!./.venv", "!./__pycache__"],
      log_level="info"
  )
