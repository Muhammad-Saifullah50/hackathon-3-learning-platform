"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.api.routes.admin import router as admin_router
from src.api.routes.profile import router as profile_router
from src.api.v1.agents import router as agents_router
from src.api.v1.code_editor import router as code_editor_router
from src.api.v1.dashboard import module_router, router as dashboard_router
from src.api.v1.quiz import router as quiz_router
from src.api.v1.code_execution import router as code_execution_router
from src.api.v1.llm import router as llm_router
from src.api.v1.teacher import router as teacher_router
from src.auth.routes import router as auth_router
from src.config import settings
from src.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


# Create FastAPI app
app = FastAPI(
    title="LearnPyByAI Authentication API",
    description="Authentication and authorization service for LearnPyByAI platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"Application starting - environment: {settings.ENVIRONMENT}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LearnPyByAI Authentication API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include authentication routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Include profile routes
app.include_router(profile_router, tags=["Profile"])

# Include admin routes
app.include_router(admin_router, tags=["Admin"])

# Include code execution routes
app.include_router(code_execution_router, tags=["Code Execution"])

# Include LLM provider routes
app.include_router(llm_router, prefix="/api/v1", tags=["LLM"])

# Include agent routes
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])

# Include code editor routes
app.include_router(code_editor_router, tags=["Code Editor"])

# Include quiz routes
app.include_router(quiz_router, tags=["Quiz"])

# Include dashboard routes (F017)
app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(module_router, prefix="/api/v1", tags=["Dashboard"])

# Include teacher routes (F019)
app.include_router(teacher_router)
