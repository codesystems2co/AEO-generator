from app.schemas import MetaTagsRequest, MetaTagsResponse


def generate_meta_tags(req: MetaTagsRequest) -> MetaTagsResponse:
    title = req.title.strip()[:70]
    description = req.description.strip()[:160]
    
    og = {
        "og:title": title,
        "og:description": description,
        "og:type": req.type,
    }
    if req.url:
        og["og:url"] = req.url
    if req.image_url:
        og["og:image"] = req.image_url
    if req.site_name:
        og["og:site_name"] = req.site_name
    
    twitter = {
        "twitter:card": "summary_large_image",
        "twitter:title": title,
        "twitter:description": description,
    }
    if req.image_url:
        twitter["twitter:image"] = req.image_url
    
    return MetaTagsResponse(
        title_tag=f"<title>{title}</title>",
        meta_description=f'<meta name="description" content="{description}">',
        og_tags=og,
        twitter_card=twitter,
        canonical=req.url,
    )
