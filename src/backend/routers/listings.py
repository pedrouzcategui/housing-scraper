from fastapi import APIRouter

router = APIRouter(tags=["listings"])


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.get("/search/{state}")
async def search(state: str):
    return {"message": f"Search endpoint for state: '{state}'"}


@router.get("/search/{state}/{city}")
async def search_city(state: str, city: str):
    return {"message": f"Search endpoint for state: '{state}' and city: '{city}'"}


@router.get("/listing/{listing_id}")
async def listing(listing_id: str):
    return {"message": f"Listing endpoint for ID: {listing_id}"}
