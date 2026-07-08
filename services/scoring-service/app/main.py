from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.consents import router as consents_router
from app.api.routes.leads import router as leads_router
from app.api.routes.pipeline import router as pipeline_router
from app.core.config import settings

app = FastAPI(title="Prospect-Assist-AI Scoring Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(leads_router)
app.include_router(consents_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "scoring-service"}
