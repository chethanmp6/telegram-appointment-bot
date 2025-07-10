"""Main FastAPI application with multi-database architecture."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Dict, Any
import time

from app.core.config import settings, app_config
from app.core.database import create_tables, check_database_health
from app.core.graph_db import init_graph_database, close_graph_database, graph_db
from app.api import appointments, telegram, knowledge, graph
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.telegram_service import TelegramService
from app.models.schemas import HealthCheck

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting application...")
    
    # Initialize services
    startup_tasks = [
        initialize_databases(),
        initialize_services(),
        initialize_telegram_bot(),
    ]
    
    try:
        await asyncio.gather(*startup_tasks)
        logger.info("Application started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down application...")
        await cleanup_services()
        logger.info("Application shutdown complete")


async def initialize_databases():
    """Initialize database connections and schemas."""
    try:
        # Initialize PostgreSQL
        await create_tables()
        logger.info("PostgreSQL database initialized")
        
        # Initialize Neo4j
        await init_graph_database()
        logger.info("Neo4j graph database initialized")
        
        # Initialize vector database (will be implemented in RAG service)
        # await init_vector_database()
        logger.info("Vector database initialization scheduled")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def initialize_services():
    """Initialize application services."""
    try:
        # Initialize LLM service
        app.state.llm_service = LLMService()
        await app.state.llm_service.initialize()
        
        # Initialize RAG service
        app.state.rag_service = RAGService()
        await app.state.rag_service.initialize()
        
        logger.info("Application services initialized")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


async def initialize_telegram_bot():
    """Initialize Telegram bot service."""
    try:
        if settings.telegram_bot_token:
            app.state.telegram_service = TelegramService()
            await app.state.telegram_service.initialize()
            logger.info("Telegram bot initialized")
        else:
            logger.warning("Telegram bot token not configured")
            
    except Exception as e:
        logger.error(f"Telegram bot initialization failed: {e}")
        raise


async def cleanup_services():
    """Cleanup application services."""
    try:
        # Close graph database
        await close_graph_database()
        
        # Close other services
        if hasattr(app.state, 'telegram_service'):
            await app.state.telegram_service.close()
        
        if hasattr(app.state, 'rag_service'):
            await app.state.rag_service.close()
            
        if hasattr(app.state, 'llm_service'):
            await app.state.llm_service.close()
            
        logger.info("All services cleaned up")
        
    except Exception as e:
        logger.error(f"Service cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Telegram Appointment Booking Bot with Agentic RAG and Graph Intelligence",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ORIGINS,
    allow_credentials=app_config.CORS_ALLOW_CREDENTIALS,
    allow_methods=app_config.CORS_ALLOW_METHODS,
    allow_headers=app_config.CORS_ALLOW_HEADERS,
)

if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your domain
    )


# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and measure response time."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
            "path": str(request.url)
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connections
        postgres_healthy = await check_database_health()
        neo4j_healthy = await graph_db.health_check()
        
        # Check services
        llm_healthy = hasattr(app.state, 'llm_service') and app.state.llm_service.is_healthy()
        rag_healthy = hasattr(app.state, 'rag_service') and app.state.rag_service.is_healthy()
        telegram_healthy = hasattr(app.state, 'telegram_service') and app.state.telegram_service.is_healthy()
        
        return HealthCheck(
            database=postgres_healthy,
            graph_db=neo4j_healthy,
            vector_db=rag_healthy,  # RAG service includes vector DB
            llm_service=llm_healthy,
            telegram_bot=telegram_healthy
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            database=False,
            graph_db=False,
            vector_db=False,
            llm_service=False,
            telegram_bot=False
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Telegram Appointment Booking Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# API routes
app.include_router(
    telegram.router,
    prefix="/api/v1/telegram",
    tags=["telegram"]
)

app.include_router(
    appointments.router,
    prefix="/api/v1/appointments",
    tags=["appointments"]
)

app.include_router(
    knowledge.router,
    prefix="/api/v1/knowledge",
    tags=["knowledge"]
)

app.include_router(
    graph.router,
    prefix="/api/v1/graph",
    tags=["graph"]
)


# Webhook endpoint for Telegram
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """Telegram webhook endpoint."""
    if token != settings.telegram_webhook_secret:
        logger.warning("Invalid webhook token")
        return JSONResponse(
            status_code=403,
            content={"error": "Invalid token"}
        )
    
    try:
        # Get update data
        update_data = await request.json()
        
        # Process update
        if hasattr(app.state, 'telegram_service'):
            await app.state.telegram_service.process_update(update_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Webhook processing failed"}
        )


# Development endpoints (only in debug mode)
if settings.debug:
    @app.get("/debug/info")
    async def debug_info():
        """Debug information endpoint."""
        return {
            "settings": {
                "app_name": settings.app_name,
                "debug": settings.debug,
                "postgres_host": settings.postgres_host,
                "neo4j_uri": settings.neo4j_uri,
                "llm_provider": settings.llm_provider,
                "vector_db_provider": settings.vector_db_provider,
            },
            "services": {
                "llm_service": hasattr(app.state, 'llm_service'),
                "rag_service": hasattr(app.state, 'rag_service'),
                "telegram_service": hasattr(app.state, 'telegram_service'),
            }
        }
    
    @app.post("/debug/reset-database")
    async def reset_database():
        """Reset database (development only)."""
        try:
            from app.core.database import reset_database
            await reset_database()
            return {"status": "Database reset successful"}
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Database reset failed"}
            )


# Add startup message
@app.on_event("startup")
async def startup_message():
    """Log startup message."""
    logger.info(f"🚀 {settings.app_name} is starting up...")
    logger.info(f"📊 Running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    logger.info(f"🌐 Server: {settings.host}:{settings.port}")
    logger.info(f"📚 API docs: http://{settings.host}:{settings.port}/docs")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )