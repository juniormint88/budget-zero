"""
Budget Zero - Personal Finance Tracker
FastAPI application entry point with routing and middleware configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, accounts, transactions, categories, dashboard, imports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs database initialization on startup and cleanup on shutdown.
    """
    # Startup: Initialize database tables
    await init_db()
    yield
    # Shutdown: cleanup would go here if needed


app = FastAPI(
    title="Budget Zero",
    description="Personal finance tracker with automatic transaction categorization",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with /api prefix
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(imports.router, prefix="/api/import", tags=["Import"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Budget Zero API", "status": "running"}


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }
