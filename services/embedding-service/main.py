from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.ENVIRONMENT == "development",
    )
