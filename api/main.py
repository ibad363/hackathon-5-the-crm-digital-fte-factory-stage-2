# api/main.py
"""
FastAPI Application for TaskVault CRM

Main entry point for the API server.
Handles webhooks, REST endpoints, and integrations.
"""

import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.webhooks import router as webhooks_router
from channels.web_form_handler import router as web_form_router
from messaging.kafka_client import KafkaClient
from channels.gmail_handler import get_gmail_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def gmail_watch_renewal_loop():
    """Background loop to renew Gmail watch every 24 hours."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.warning("⚠️ GOOGLE_CLOUD_PROJECT not set. Gmail auto-renewal disabled.")
        return

    while True:
        try:
            handler = get_gmail_handler()
            result = await handler.setup_push_notifications(project_id)
            logger.info(f"🔄 Gmail watch renewed automatically. Next renewal in 24h. HID: {result.get('historyId')}")
        except Exception as e:
            logger.error(f"❌ Failed to renew Gmail watch: {e}")

        # Wait 24 hours (86400 seconds)
        await asyncio.sleep(86400)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 TaskVault CRM API starting up...")
    logger.info("📧 Gmail webhook ready at: /api/webhooks/gmail")
    logger.info("📱 WhatsApp webhook ready at: /api/webhooks/whatsapp")
    logger.info("🌐 Web form endpoint ready at: /api/support/submit")

    # Start the Gmail watch renewal loop in the background
    renewal_task = asyncio.create_task(gmail_watch_renewal_loop())

    yield

    # Shutdown
    logger.info("👋 TaskVault CRM API shutting down...")
    renewal_task.cancel()
    await KafkaClient.shutdown()


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
