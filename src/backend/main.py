from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.routers.listings import router as listings_router
from backend.routers.users import router as users_router
from db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(listings_router)