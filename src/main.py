from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from src.api.routes import todo, reminder, calendar_event, call, webhook
from src.models.database import create_tables

logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting application, initializing database...")
    create_tables()
    logger.info("Application startup complete!")
    yield
    logger.info("Application shutdown")

app = FastAPI(title="Personal Assistant Voice Agent", lifespan=lifespan)

# Add CORS middleware to allow web-based calls from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Hide TODO, Reminder, and Calendar Event endpoints from Swagger docs
app.include_router(todo.router, include_in_schema=False)
app.include_router(reminder.router, include_in_schema=False)
app.include_router(calendar_event.router, include_in_schema=False)

# Keep Call endpoints visible in Swagger
app.include_router(call.router)
app.include_router(webhook.router)

# Serve test page for web calls
@app.get("/test-call")
async def test_call_page():
    """Serve the web call test page"""
    from pathlib import Path
    html_path = Path(__file__).resolve().parent.parent / "test_web_call.html"
    return FileResponse(str(html_path), media_type="text/html")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)