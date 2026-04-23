from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers.companies import router as companies_router
from app.routers.company_types import router as company_types_router
from app.routers.health import router as health_router
from app.routers.raw_articles import router as raw_articles_router
from app.routers.sources import router as sources_router
from app.routers.source_types import router as source_types_router
from app.routers.stats import router as stats_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Backend API for the AI Product Radar MVP.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(stats_router, prefix="/api")
    app.include_router(companies_router, prefix="/api")
    app.include_router(sources_router, prefix="/api")
    app.include_router(company_types_router, prefix="/api")
    app.include_router(source_types_router, prefix="/api")
    app.include_router(raw_articles_router, prefix="/api")
    return app


app = create_app()
