from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .router.message import router as message_router

app = FastAPI(title="Gift App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_host.rstrip("/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok"}
