from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from src.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cycling Trip Planner",
        description="AI agent for planning multi-day cycling trips",
        version="0.1.0",
    )
    app.include_router(router)
    return app


app = create_app()
