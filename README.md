# AEO / SEO / GEO Generator

A Docker-based tool with a modern UI and REST API for **AEO** (Answer Engine Optimization), **SEO** (Search Engine Optimization), and **GEO** (Generative Engine Optimization): meta tags, keyword extraction, content analysis, AEO suggestions, SEO scoring, and optimization for AI-powered search engines.

All commands below assume you are in the project root (the directory that contains `docker-compose.yml`).

## Features

- **Meta tags** — Generate `<title>`, meta description, Open Graph, and Twitter Card tags
- **Keywords** — Extract keywords and density (frequency-based or **NLP RAKE**)
- **Content analysis** — Word count, reading time, headings, keyword density, **readability (Flesch, SMOG, ARI)**, recommendations
- **AEO suggestions** — Structure and Q&A ideas for AI answer engines (e.g. ChatGPT, Perplexity)
- **SEO score** — Score and checklist for title, meta description, and content length
- **NLP** — RAKE keyword extraction and standalone readability metrics
- **URL analyzer** — Fetch a URL and extract meta, headings, and word count
- **External SEO APIs** — Optional Moz (DA/PA) and SEMrush (domain rank); set `MOZ_API_TOKEN` or `MOZ_ACCESS_ID`/`MOZ_SECRET_KEY`, and `SEMRUSH_API_KEY`
- **GEO (Generative Engine Optimization)** — Optimize content for AI search engines (ChatGPT, Perplexity, Google AI Overviews): analyze for citations, statistics, authoritative language, quotable definitions, Q&A format; get optimization templates and citation enhancement suggestions

## Quick start with Docker

From the project root (`AEO-generator/`):

```bash
docker compose up --build
```

- **UI:** http://localhost:5173  
- **API docs:** http://localhost:8000/docs  

The frontend proxies `/api` to the backend, so use the UI at 5173 and all API calls go through it.

## How to add SEO/AEO to your website, app, or product

Use the tool to **generate** meta and **analyze** content; then **add the outputs** to your pages and **structure** content for both search and answer engines.

| Step | What to do |
|------|------------|
| **1. Meta tags** | Use **Meta Tags** (or `/api/meta/generate`) to create title + description. Put them in your HTML `<head>`, CMS SEO fields, or SPA metadata (e.g. Next.js `metadata`, React Helmet). Add Open Graph and Twitter tags if you share links. |
| **2. Structure** | Use **AEO Suggest** for your topic → take the suggested sections as H2/H3 and the Q&A ideas as an FAQ block. One H1 per page; clear headings help both Google and AI answer engines. |
| **3. Keywords** | Use **Keywords** or **NLP (RAKE)** on your draft (or a competitor URL via **URL Analyze**) → put the main phrase in title, meta, first paragraph, and headings. Keep density natural (~1–2% for main term). |
| **4. Readability & score** | Paste your draft into **Content Analysis** (readability, word count, recommendations) and **SEO Score** (title/meta length, content length, headings). Fix issues before publishing. |
| **5. GEO optimization** | Use **GEO → Analyze Content** to check for AI citation factors (statistics, sources, quotable definitions). Use **Get Suggestions** for templates and **Enhance Citations** to find sentences needing improvement. |
| **6. Integrate** | Call the REST API from your backend, CMS, or CI to generate meta, get AEO outlines, or score content automatically. |

**Full guide:** See **[How to add SEO & AEO to your site](docs/How_To_Add_SEO_AEO_To_Your_Site.md)** for detailed steps for websites (HTML, CMS, React, Next.js), apps (meta, app store copy), and products (help docs, landing pages), plus a checklist and API integration examples.

## Run API only

From the project root:

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open http://localhost:8000/docs for the API.

## API overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/meta/generate` | POST | Generate meta tags (title, description, OG, Twitter) |
| `/api/keywords/extract` | POST | Extract keywords and density from text |
| `/api/analysis/content` | POST | Analyze content (word count, reading time, recommendations) |
| `/api/aeo/suggest` | POST | Get AEO structure and Q&A suggestions for a topic |
| `/api/score/calculate` | POST | Calculate SEO score and checklist |
| `/api/nlp/keywords` | POST | RAKE keyword extraction |
| `/api/nlp/readability` | POST | Readability metrics (Flesch, SMOG, ARI) |
| `/api/url/analyze` | POST | Fetch URL and extract meta/headings/word count |
| `/api/external/moz` | POST | Moz URL metrics (requires Moz API key) |
| `/api/external/semrush` | POST | SEMrush domain overview (requires SEMrush API key) |
| `/api/geo/analyze` | POST | Analyze content for GEO factors (citations, stats, authority) |
| `/api/geo/optimize` | POST | Get GEO optimization templates for a topic |
| `/api/geo/citations` | POST | Suggest citation enhancements for content |
| `/health` | GET | Health check |

### Example: generate meta tags

```bash
curl -X POST http://localhost:8000/api/meta/generate \
  -H "Content-Type: application/json" \
  -d '{"title":"My Page","description":"A short description.","url":"https://example.com/page"}'
```

### Example: SEO score

```bash
curl -X POST http://localhost:8000/api/score/calculate \
  -H "Content-Type: application/json" \
  -d '{"title":"My Title","meta_description":"A 120-160 char description.","content":"Your long page content here..."}'
```

### Example: GEO analyze

```bash
curl -X POST http://localhost:8000/api/geo/analyze \
  -H "Content-Type: application/json" \
  -d '{"content":"Your content here. According to research, 85% of users prefer content with statistics. Studies show that citations improve credibility."}'
```

## Project structure

```
├── docker-compose.yml   # API + frontend
├── api/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── app/
│       ├── config.py
│       ├── schemas.py
│       ├── routers/    # Meta, Keywords, Analysis, AEO, Score, GEO
│       └── services/   # Business logic
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api.js      # API client
        ├── App.jsx
        ├── components/
        └── tabs/       # MetaTags, Keywords, ContentAnalysis, AEO, SEOScore, Geo
```

## Tech stack

- **API:** FastAPI, Pydantic, Uvicorn; NLP: rake-nltk, NLTK, textstat; HTTP/HTML: requests, Beautiful Soup
- **Frontend:** React 18, Vite
- **Deploy:** Docker Compose (API on 8000, frontend on 5173)

## Documentation

- **[How to add SEO & AEO to your site](docs/How_To_Add_SEO_AEO_To_Your_Site.md)** — Step-by-step guide: where to put meta tags (HTML, CMS, React, Next.js, apps), how to structure content and FAQ, use keywords, check readability, and integrate the API into your app or product.
- **Guide in the UI:** The **Guide** tab (first tab) in the web app at http://localhost:5173 shows the full "How to add SEO & AEO to your site" guide. The content is served from `frontend/public/guide.md` (copy of `docs/How_To_Add_SEO_AEO_To_Your_Site.md`).
- **Academic paper:** A ~6,800-word journal-style paper describing the system (architecture, NLP, external APIs, GEO module, limitations) is in `docs/Academic_Paper_AEO_SEO_Generator.md`.
