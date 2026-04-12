# api/main.py
"""
FastAPI Application for TaskVault CRM

Main entry point for the API server.
Handles webhooks, REST endpoints, and integrations.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.webhooks import router as webhooks_router
from channels.web_form_handler import router as web_form_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 TaskVault CRM API starting up...")
    logger.info("📧 Gmail webhook ready at: /api/webhooks/gmail")
    logger.info("📱 WhatsApp webhook ready at: /api/webhooks/whatsapp")
    logger.info("🌐 Web form endpoint ready at: /api/support/submit")

    yield

    # Shutdown
    logger.info("👋 TaskVault CRM API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="TaskVault CRM API",
    description="Customer Success Digital FTE API for TaskVault",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(web_form_router, prefix="/api")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "service": "taskvault-crm-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TaskVault CRM API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
