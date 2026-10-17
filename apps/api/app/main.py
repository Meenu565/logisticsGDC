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

    # Note: Middlewares execute in reverse order of addition.
    # We add CORSMiddleware LAST so it wraps everything as the outermost layer,
    # ensuring all requests (including preflight OPTIONS and errors) carry CORS headers.
    app.add_middleware(AgentRequestLogMiddleware)
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    from fastapi import Request
    from fastapi.responses import JSONResponse
    import logging

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logging.getLogger("uvicorn.error").error(f"Global exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(exc)},
        )

    return app


app = create_app()
