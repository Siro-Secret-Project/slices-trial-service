from fastapi import APIRouter,Response, status
from document_retrieval.models.models import SearchResult, BaseResponse, SearchDocuments
from document_retrieval.services.fetch_documents_service import fetch_documents_service
from document_retrieval.services.fetch_similar_documents_extended import fetch_similar_documents_extended

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
        similarity_threshold = request.similarity_threshold
        module = request.module

        # Fetch similar documents
        similar_documents_response = await fetch_documents_service(query=input_query,
                                                                   similarity_threshold=similarity_threshold,
                                                                   module=module)
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
        base_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return base_response


@router.post("/search_documents_new", response_model=BaseResponse)
async def search_routes_new(request: SearchDocuments, response: Response):
    """
    Endpoint to search for documents based on inclusion criteria, exclusion criteria, and rationale.

    Args:
        request (SearchDocuments): The request body containing search criteria.
        response (Response): The FastAPI Response object.

    Returns:
        BaseResponse: A standardized response containing the search results or an error message.
    """
    base_response = BaseResponse(
        success=False,
        status_code=status.HTTP_400_BAD_REQUEST,
        data=None,
        message="Internal Server Error",
    )

    try:
        # Extract and sanitize input criteria
        inclusion_criteria = request.inclusion_criteria if request.inclusion_criteria != "" else None
        exclusion_criteria = request.exclusion_criteria if request.exclusion_criteria != "" else None
        rationale = request.rationale if request.rationale != "" else None

        input_document = {
            "inclusion_criteria": inclusion_criteria,
            "exclusion_criteria": exclusion_criteria,
            "rationale": rationale,
        }

        # Fetch similar documents based on the input criteria
        similar_documents_response = await fetch_similar_documents_extended(documents_search_keys=input_document)

        # Handle the response from the fetch function
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
        # Handle unexpected errors and log them
        print(f"Unexpected error: {e}")
        base_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        base_response.message = f"Unexpected error: {e}"
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return base_response

