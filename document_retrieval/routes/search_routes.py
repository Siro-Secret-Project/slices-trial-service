from fastapi import APIRouter,Response, status
from document_retrieval.models.models import SearchResult, BaseResponse
from document_retrieval.services.fetch_documents_service import fetch_documents_service

router = APIRouter()

@router.post("/search_documents", response_model=BaseResponse)
async def search_routes(request: SearchResult, response: Response):
    base_response = BaseResponse(
        success=False,
        status_code=status.HTTP_400_BAD_REQUEST,
        data=None,
        message="Internal Server Error",
    )
    try:
        input_query = request.search_query
        embedding_model = request.embedding_model
        similarity_threshold = request.similarity_threshold
        # module = request.module

        # Fetch similar documents
        similar_documents_response = await fetch_documents_service(query=input_query,
                                                                   similarity_threshold=similarity_threshold,
                                                                   embedding_model=embedding_model)
        if similar_documents_response["success"] is False:
            base_response.success = False
            base_response.message = similar_documents_response["message"]
            response.status_code = status.HTTP_400_BAD_REQUEST
            return base_response
        else:
            base_response.success = True
            base_response.message = similar_documents_response["message"]
            base_response.status_code = status.HTTP_200_OK
            base_response.data = similar_documents_response["data"]
            response.status_code = status.HTTP_200_OK
            return base_response
    except Exception as e:
        print(f"Unexpected error: {e}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        base_response.message = f"Unexpected error: {e}"
        return base_response