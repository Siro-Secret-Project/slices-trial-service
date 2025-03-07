import os
import logging
from typing import Dict, Any
from document_retrieval.utils.pdf_extraction.extract_index_keys import extract_index_keys
from document_retrieval.utils.pdf_extraction.extract_sections import extract_sections
from document_retrieval.utils.pdf_extraction import pdf_modular_functions

# Setup Logger
logger = logging.getLogger("document_retrieval")
logger.setLevel(logging.DEBUG)



async def pdf_extraction_service(file) -> Dict[str, Any]:
    """Extracts structured data from a PDF."""
    response = {"success": False, "message": "PDF extraction failed", "data": None}
    try:
        validation_result = pdf_modular_functions.validate_pdf(file)
        if not validation_result["success"]:
            response["message"] = validation_result["message"]
            logger.error(response["message"])
            return response

        temp_file_path = pdf_modular_functions.save_temp_file(file)
        upload_response = pdf_modular_functions.process_s3_upload(temp_file_path)
        if not upload_response["success"]:
            response["message"] = upload_response["message"]
            logger.error(response["message"])
            return response

        index_file_response = pdf_modular_functions.download_index_file()
        if not index_file_response["success"]:
            response["message"] = index_file_response["message"]
            logger.error(response["message"])
            return response

        index_keys = extract_index_keys("index.pdf")
        sections = extract_sections(pdf_path=temp_file_path, index_keys=index_keys)
        mapping = pdf_modular_functions.get_index_mapping(index_keys)
        final_data = pdf_modular_functions.map_sections_to_targets(sections, mapping)

        response["data"] = final_data
        response["success"] = True
        os.unlink(temp_file_path)
        os.unlink("index.pdf")
        return response
    except Exception as error:
        logger.exception("Error in PDF extraction service")
        response["message"] = str(error)
        return response