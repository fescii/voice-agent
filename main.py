"""
FastAPI AI Voice Agent System
Main application entry point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import router as api_v1_router
from core.config.app.main import AppConfig
from core.logging.setup import setup_logging
from wss.endpoint import websocket_router

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Setup logging
    setup_logging()
    
    # Load app configuration
    config = AppConfig()
    
    # Create FastAPI app
    app = FastAPI(
        title=config.app_name,
        version=config.version,
        debug=config.debug_mode,
        description="AI Voice Agent System with Ringover Integration"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
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
        port=8000,
        reload=config.debug_mode,
        log_level="info"
    )
