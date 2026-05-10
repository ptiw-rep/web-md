from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.config import get_settings
from app.db import init_db
from app.routes import convert, admin
from app.auth import verify_api_key

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    await init_db()
    logging.getLogger("app").info("🗄️ SQLite database initialized")
    logging.getLogger("app").info(f"🚀 Starting md-exporter v2.0 ({settings.environment})")
    yield
    logging.getLogger("app").info("🛑 Shutting down")

def create_app() -> FastAPI:
    app = FastAPI(title="Webpage → Markdown Exporter", version="2.0.0", lifespan=lifespan)

    # CORS Configuration (dynamic from env vars)
    cors_origins = settings.cors_allow_origins_list
    if cors_origins:  # Only add middleware if origins are configured
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods_list,
            allow_headers=settings.cors_allow_headers_list,
            expose_headers=settings.cors_expose_headers_list,
            max_age=600,  # Cache preflight for 10 minutes
        )

    if not settings.is_production:
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    app.include_router(convert.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
    app.include_router(admin.router, prefix="/api/v1")

    @app.get("/health")
    async def health(): return {"status": "healthy", "env": settings.environment}

    @app.exception_handler(Exception)
    async def global_exc(request: Request, exc: Exception):
        logging.getLogger("app").error(f"Unhandled: {exc}", exc_info=True)
        return JSONResponse(500, {"detail": "Internal server error"})
    return app

app = create_app()