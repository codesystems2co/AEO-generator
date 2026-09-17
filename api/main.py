from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    meta,
    keywords,
    content_analysis,
    aeo,
    seo_score,
    nlp,
    url_analyzer,
    external_seo,
    geo,
    chat,
    google_search,
    packs,
    connectors,
    wizard,
    entitlement,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="AEO/SEO Generator API",
    description="Generate and analyze AEO (Answer Engine Optimization) and SEO content",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = settings.cors_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router, prefix="/api/meta", tags=["Meta Tags"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])
app.include_router(content_analysis.router, prefix="/api/analysis", tags=["Content Analysis"])
app.include_router(aeo.router, prefix="/api/aeo", tags=["AEO"])
app.include_router(seo_score.router, prefix="/api/score", tags=["SEO Score"])
app.include_router(nlp.router, prefix="/api/nlp", tags=["NLP"])
app.include_router(url_analyzer.router, prefix="/api/url", tags=["URL Analyzer"])
app.include_router(external_seo.router, prefix="/api/external", tags=["External SEO APIs"])
app.include_router(geo.router)
app.include_router(chat.router, prefix="/api/chat", tags=["Chat IA"])
app.include_router(google_search.router, prefix="/api/google", tags=["Google Search"])
app.include_router(packs.router, prefix="/api/packs", tags=["Ollama Packs"])
app.include_router(connectors.router, prefix="/api/connectors", tags=["Connectors"])
app.include_router(wizard.router, prefix="/api/wizard", tags=["Wizard"])
app.include_router(entitlement.router, prefix="/api/entitlement", tags=["Entitlement"])


@app.get("/")
async def root():
    return {"service": "AEO/SEO Generator API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    return {"status": "ok"}
