# How to Add SEO & AEO to Your Website, App, or Product

This guide shows how to use the AEO/SEO Generator to add search and answer-engine optimization to your website, app, or product content.

---

## 1. Add meta tags to your pages

Meta tags tell search engines and social platforms what your page is about. Use the tool’s **Meta Tags** tab or `POST /api/meta/generate` to create them, then put the output in your HTML or app.

### Websites (HTML / CMS)

**Where:** In the `<head>` of every page (or in your template/layout).

1. Open the tool → **Meta Tags** (or call the API with your title and description).
2. Copy the generated HTML.
3. Paste it into your page’s `<head>`:

```html
<head>
  <meta charset="UTF-8" />
  <title>Your Page Title (30–60 chars)</title>
  <meta name="description" content="Your 120–160 character description." />
  <!-- Open Graph (Facebook, LinkedIn, etc.) -->
  <meta property="og:title" content="Your Page Title" />
  <meta property="og:description" content="Your description." />
  <meta property="og:url" content="https://yoursite.com/page" />
  <meta property="og:type" content="website" />
  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Your Page Title" />
  <meta name="twitter:description" content="Your description." />
  <!-- Canonical (recommended) -->
  <link rel="canonical" href="https://yoursite.com/page" />
</head>
```

- **CMS (WordPress, Webflow, etc.):** Use the SEO / meta fields in the page or post editor; the CMS will output these tags. Generate the text in our tool, then paste into those fields.
- **Static site (Hugo, Jekyll, Astro):** Put title and description in front matter; your theme should render `<title>` and `<meta name="description">`. Use the tool to write and length-check them.

### Single-page apps (React, Vue, Next.js)

- **Next.js:** Use `next/head` or the App Router `metadata` (or `generateMetadata`) so each route has its own `<title>` and `<meta name="description">`. Generate copy in the tool, then set it in code.
- **React (CRA, Vite) / Vue:** Use a document-head helper (e.g. `react-helmet`, `vue-meta`) or a library like `react-helmet-async` so each view can set title and meta. Call our API from a build script or admin UI to get suggested meta, then hardcode or feed from CMS.

**Example (Next.js App Router):**

```js
// app/products/page.js
export const metadata = {
  title: 'Products – Your Brand',        // from tool, 30–60 chars
  description: 'Short description 120–160 chars from the tool.',
  openGraph: {
    title: 'Products – Your Brand',
    description: 'Short description.',
    url: 'https://yoursite.com/products',
  },
}
```

### Mobile / native apps

- **Web views:** If you show web content in-app, use the same meta tags in that HTML so crawlers and link previews see the right title and description.
- **App store listings:** Use the tool to draft short, clear titles and descriptions (then trim to store limits). AEO-style clarity helps both humans and any AI that summarizes your app.

**Takeaway:** Every public page or screen that can be linked should have a unique title and description; generate and length-check them with the Meta Tags tool.

---

## 2. Structure content for SEO and AEO

Structure helps both search engines and AI answer engines (e.g. ChatGPT, Perplexity) understand and cite your content.

### Use the AEO Suggest tab

1. Open **AEO Suggest** and enter your page topic (e.g. “how to set up two-factor authentication”).
2. Use the tool’s output:
   - **Suggested title** → Use as or refine your `<title>` and H1.
   - **Key entities** → Use these terms consistently in the page.
   - **Q&A suggestions** → Turn into a real FAQ section (see below).
   - **Structured sections** → Use as your H2/H3 outline.

### Add a clear H1 and headings

- One **H1** per page (the main topic). Match the intent of your title/meta.
- **H2/H3** for sections. Use the AEO “structured sections” as a starting point, e.g.:
  - Introduction / What is X?
  - How it works / Steps
  - Examples / Use cases
  - Best practices / Tips
  - Summary / Next steps

### Add an FAQ / Q&A block (strong for AEO)

AI answer engines often surface FAQ-style content. Use **AEO Suggest** to get question–answer ideas, then add a real FAQ on the page:

- **HTML:** Use headings for questions and paragraphs for answers; optionally wrap in a `<section>` or schema (see below).
- **Schema (optional):** Add [FAQPage](https://developers.google.com/search/docs/appearance/structured-data/faqpage) JSON-LD so search engines can show your Q&A in results.

**Takeaway:** One H1, logical H2/H3, and a short FAQ section improve both SEO and AEO. Use the AEO tool to draft structure and Q&A.

---

## 3. Use the right keywords in your content

Keywords help search engines (and often answer engines) match your page to queries.

### Find keywords with the tool

1. **Keywords** tab: Paste existing draft content → get frequency-based keywords and density.
2. **NLP** tab → RAKE: Paste the same (or competitor) content → get phrase-level keywords (e.g. “two-factor authentication”, “password security”).
3. **URL Analyze:** Enter a competitor URL → see their headings and word count; use that to inspire your own outline and terms.

### Where to use keywords

- **Title:** Include the main keyword or phrase (from the tool) near the start.
- **Meta description:** Include the main keyword naturally; keep 120–160 characters.
- **First paragraph:** Mention the main topic and key phrase early.
- **Headings:** Use variations of your key phrases in H2/H3 (don’t stuff).
- **Body:** Use keywords naturally; aim for ~1–2% density for the main term (Content Analysis tab shows density and suggestions).

**Takeaway:** Use **Keywords** and **NLP (RAKE)** to choose and check keywords; put the main one in title, meta, first paragraph, and headings.

---

## 4. Check readability and length

Answer engines and users both prefer clear, scannable content.

### Use Content Analysis

1. Paste your draft into **Content Analysis** (optionally set a target keyword).
2. Use the feedback:
   - **Word count:** Prefer 300+ words per page; 1000+ for important topics.
   - **Reading time:** Keep in mind (e.g. ~200 words/min); shorten if too long.
   - **Readability (NLP):** Flesch, SMOG, ARI and the short interpretation. If it says “difficult”, shorten sentences and simplify words.
   - **Recommendations:** Add headings, shorten paragraphs, adjust keyword density.

### Use SEO Score

1. Enter your **title**, **meta description**, and **content** in **SEO Score**.
2. Fix what fails: title length 30–60, meta 120–160, enough content, presence of headings.

**Takeaway:** Run **Content Analysis** and **SEO Score** before publishing; improve readability and hit the length/heading checks.

---

## 5. Integrate the tool into your app or product

You can use the REST API from your own backend, CLI, or admin UI.

### From your backend (e.g. Node, Python)

Call the API when generating or validating content:

```bash
# Generate meta for a new page
curl -X POST http://your-api-host:8000/api/meta/generate \
  -H "Content-Type: application/json" \
  -d '{"title":"Your Title","description":"Your description","url":"https://yoursite.com/page"}'

# Score existing content
curl -X POST http://your-api-host:8000/api/score/calculate \
  -H "Content-Type: application/json" \
  -d '{"title":"...","meta_description":"...","content":"..."}'

# Get AEO suggestions for a topic
curl -X POST http://your-api-host:8000/api/aeo/suggest \
  -H "Content-Type: application/json" \
  -d '{"topic":"your topic"}'
```

Use the JSON responses to:

- Pre-fill meta fields in your CMS or admin.
- Show an “SEO score” or “readability” badge in the editor.
- Suggest an outline (from AEO) when creating a new page.

### From a static site or CI

- **Build script:** For each page (e.g. from front matter or a content JSON), call `/api/meta/generate` and optionally `/api/score/calculate`; write the meta into the built HTML or fail the build if score is below a threshold.
- **Preview:** In a preview environment, call `/api/url/analyze` with the preview URL to confirm title, description, and headings after build.

### From a product (help docs, landing pages)

- **Help center / docs:** For each article, run **AEO Suggest** with the topic → use suggested sections and Q&A as the outline; then run **Content Analysis** and **SEO Score** on the draft. Store suggested meta in your docs CMS and render it in the layout.
- **Landing pages:** Use **Meta Tags** and **SEO Score** for every landing variant; use **Keywords** to align copy with campaign terms.
- **Product pages:** One meta set per product (title + description from the tool); keep structure clear (H1 = product name, H2 = key benefits, then FAQ).

**Takeaway:** Use the API from your backend, build, or admin to generate meta, scores, and AEO outlines so SEO/AEO are part of your normal workflow.

---

## 6. Quick checklist: add SEO/AEO to a new page

- [ ] **Topic:** Decide the main topic; run **AEO Suggest** and use suggested title, sections, and Q&A ideas.
- [ ] **Title & meta:** Use **Meta Tags** to create a 30–60 char title and 120–160 char description; add them to your HTML/CMS/SPA (and OG/Twitter if you share the page).
- [ ] **Canonical:** Set `<link rel="canonical" href="...">` to the final URL (or equivalent in your framework).
- [ ] **Structure:** One H1; H2/H3 from AEO sections; add a short FAQ from AEO Q&A.
- [ ] **Keywords:** Run **Keywords** or **NLP (RAKE)** on a draft or competitor; put main phrase in title, meta, first paragraph, and headings.
- [ ] **Draft:** Write the body; keep sentences and paragraphs short; use key terms naturally.
- [ ] **Check:** Run **Content Analysis** (readability, word count, recommendations) and **SEO Score** (title, meta, length, headings); fix issues.
- [ ] **Deploy:** After deploy, optionally run **URL Analyze** on the live URL to confirm meta and structure.

Use this checklist for every new page or major update so your website, app, or product stays optimized for both search and answer engines.
