from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import captions
from pythainlp.transliterate import transliterate
app = FastAPI(title="YouTube Subtitles Downloader", version="1.0.0")

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
