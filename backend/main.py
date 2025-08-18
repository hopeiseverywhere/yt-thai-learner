from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import captions,learn
from config.settings import settings
import uvicorn

from services.dictionary_service import dict_service

app = FastAPI(title=settings.api_title, version=settings.api_version)

# --- CORS (adjust origins as needed) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(captions.router, prefix="/captions", tags=["captions"])
app.include_router(learn.router, prefix="/learn", tags=["learn"])

@app.on_event("startup")
async def startup_event():
    dict_service.load_dictionary_from_file()


@app.get("/")
def root():
    return {
        "message": "YouTube Subtitles Downloader API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Run with: uvicorn main:app --reload ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True
    )
