"""
EquityIQ FastAPI Application Entry Point.
"""

import logging

from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("equityiq")

app = FastAPI(
    title="EquityIQ API",
    description="Investment Analysis and Research Platform Core API",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify system status.
    """
    logger.info("Health check endpoint hit")
    return {"status": "healthy"}
