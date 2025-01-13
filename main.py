from fastapi import FastAPI
from document_retrieval.routes import search_routes

app = FastAPI()

app.include_router(search_routes.router, prefix="/api/v1/ml", tags=["search"])

@app.get("/")
async def root():
    return {"message": "Python Backend Services Running"}