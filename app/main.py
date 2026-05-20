from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import init_db
#from app.routers.welfare import router as welfare_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.chat import router as chat_router

app = FastAPI(
    title=settings.app_name,
    description="복지 OpenAPI 데이터를 수집하고 PostgreSQL에 저장하는 FastAPI 서버",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "message": "FastAPI Welfare Project",
        "docs": "/docs",
    }


#app.include_router(welfare_router)
app.include_router(chat_router)
