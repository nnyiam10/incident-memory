from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.routes import incidents, investigations, memories

app = FastAPI(title="Incident Memory API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000","http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
app.include_router(investigations.router, prefix="/investigations", tags=["investigations"])
app.include_router(memories.router, prefix="/memories", tags=["memories"])

@app.get("/health")
def health(): return {"status": "ok", "mode": "safe-diagnostics"}

