"""NetCoop AI backend entry point.

Run from the backend/ folder:   uvicorn main:app --reload
Interactive API docs:           http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from api.routes import router
from protocols.validator import ProtocolError

app = FastAPI(
    title="NetCoop AI",
    description="Multi-agent network fault diagnosis and interoperability",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.exception_handler(ProtocolError)
async def protocol_error_handler(_: Request, exc: ProtocolError):
    """Protocol violations are the client's fault -> 422, not 500."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/", tags=["system"])
def root():
    return {"name": "NetCoop AI", "docs": "/docs", "health": "/api/health"}
