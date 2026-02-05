from fastapi import APIRouter
from app.schemas import MetaTagsRequest, MetaTagsResponse
from app.services.meta_service import generate_meta_tags

router = APIRouter()


@router.post("/generate", response_model=MetaTagsResponse)
async def generate_meta(req: MetaTagsRequest):
    return generate_meta_tags(req)
