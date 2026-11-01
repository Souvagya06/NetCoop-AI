import os
"""NetCoop AI backend entry point.

Run from the backend/ folder:   uvicorn main:app --reload
Or directly with Python:        python main.py
Interactive API docs:           http://127.0.0.1:8000/docs
Frontend Web Dashboard:         http://127.0.0.1:8000
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "code": "protocol_error"},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_: Request, exc: RequestValidationError):
    """Keep validation errors parseable without echoing submitted values."""
    errors = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "code": "request_validation_error",
            "errors": errors,
        },
    )


# --- Frontend Static Files & SPA Integration ---
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")


@app.get("/", include_in_schema=False)
def serve_root():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {
        "name": "NetCoop AI",
        "docs": "/docs",
        "health": "/api/health",
        "frontend": "Not built yet. Run 'npm --prefix frontend run build' to build the UI.",
    }


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    # Don't intercept API, documentation, or openapi schema
    if full_path.startswith(("api/", "docs", "openapi.json")):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    file_path = FRONTEND_DIST / full_path
    if file_path.is_file():
        return FileResponse(file_path)

    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return JSONResponse(status_code=404, content={"detail": f"File not found: {full_path}"})


if __name__ == "__main__":
    import uvicorn
    import sys

    backend_dir = str(Path(__file__).resolve().parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    print("\n" + "=" * 60)
    print("  NetCoop AI is running!")
    print("  - Web Dashboard: http://127.0.0.1:8000")
    print("  - API Docs:      http://127.0.0.1:8000/docs")
    print("  - Health Check:  http://127.0.0.1:8000/api/health")
    print("=" * 60 + "\n")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
