from fastapi import FastAPI
from sqlalchemy import text

from app.db.base import Base
from app.models.analysis import Analysis

from app.api.analysis import router as analysis_router

from app.db.session import engine

app = FastAPI(
    name="AI Search Visibility Intelligence Platform",
    description="A platform that provides AI-powered search visibility intelligence for businesses and marketers.",
    version="0.1.0"
)
Base.metadata.create_all(bind=engine)

app.include_router(analysis_router)

@app.get("/")
def root():
    return{"message": "welcome to the AI search visibility intelligence platform!"}

@app.get("/health")
def health_check():
    return {
        "status":"healthy"
    }

@app.get("/health/db")
def db_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return{
            "database":"connected",
            "result":result.scalar()
        }
