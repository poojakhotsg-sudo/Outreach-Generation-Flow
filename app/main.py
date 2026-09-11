from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import research, problems, offer, outreach

app = FastAPI(title="Outreach Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api")
app.include_router(problems.router, prefix="/api")
app.include_router(offer.router, prefix="/api")
app.include_router(outreach.router, prefix="/api")

app.mount("/", StaticFiles(directory="public", html=True), name="static")
