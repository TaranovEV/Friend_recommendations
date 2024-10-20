from fastapi import FastAPI

from api.models.handlers import router as models_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Recomendation Service",
        docs_url="/api/docs",
        description="A simple recomendation Service",
        debug=True,
    )
    app.include_router(models_router, prefix="/models")
    return app
