from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mood_router

app = FastAPI(title="Mood Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://mood-matcher-9yvc.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mood_router.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "mood-matcher-api"}
