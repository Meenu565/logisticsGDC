from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.auth import ApiKeyMiddleware
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import AgentRequestLogMiddleware


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(AgentRequestLogMiddleware)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
