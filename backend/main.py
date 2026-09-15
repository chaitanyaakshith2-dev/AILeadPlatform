from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leads import router as leads_router
from public import router as public_router
from settings import router as settings_router

app = FastAPI(title="LeadFlow AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://aileadplatform.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router)
app.include_router(settings_router)
app.include_router(public_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}