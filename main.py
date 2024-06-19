import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app="web.app:app",
        host='0.0.0.0',
        port=8000,
        reload=True,
        workers=1
    )
