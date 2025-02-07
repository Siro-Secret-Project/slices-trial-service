# Slices Trial Service

This is a Python backend using FastAPI with a microservice architecture. 

## Key Features
- Embedding generation with BioBERT or OpenAI models.
- Pinecone integration for similarity search.
- Modular microservice structure with routes, services, and providers.

## How to Run
1. Install dependencies: `poetry install`
2. Start the server: `uvicorn main:app --reload`
3. Access the API at `http://localhost:8000`

## Endpoints
- `/search_documents`: It processes text input, converts it into embeddings, and queries a Pinecone database to return the NCT ID of the most similar documents
