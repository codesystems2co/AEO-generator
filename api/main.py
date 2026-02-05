from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import meta, keywords, content_analysis, aeo, seo_score, nlp, url_analyzer, external_seo, geo

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
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


@app.get("/")
async def root():
    return {"service": "AEO/SEO Generator API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    return {"status": "ok"}
