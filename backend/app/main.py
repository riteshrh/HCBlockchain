
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Blockchain API",
    version="1.0.0",
    description="Secure medical records management system with blockchain integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api import auth, records, consent, blockchain, admin
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(records.router, prefix="/api/v1/records", tags=["Records"])
app.include_router(consent.router, prefix="/api/v1/consent", tags=["Consent"])
app.include_router(blockchain.router, prefix="/api/v1/blockchain", tags=["Blockchain"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# Serve blockchain UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/blockchain-explorer")
    async def blockchain_explorer():
        ui_file = static_dir / "blockchain_ui.html"
        if ui_file.exists():
            return FileResponse(str(ui_file))
        return {"error": "Blockchain UI not found"}

# TODO: Add other routers as they are implemented
# from app.api import audit, providers
# app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
# app.include_router(providers.router, prefix="/api/v1/providers", tags=["Providers"])

@app.get("/")
async def root():
    return {
        "message": "Healthcare Blockchain API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "healthcare-blockchain-api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
