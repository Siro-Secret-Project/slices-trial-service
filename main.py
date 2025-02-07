from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from document_retrieval.routes import search_routes

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(search_routes.router, prefix="/api/v1/ml", tags=["search"])

@app.get("/")
async def root():
    return {"message": "Python Backend Services Running"}
