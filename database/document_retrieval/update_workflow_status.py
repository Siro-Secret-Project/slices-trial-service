from datetime import datetime
from database.mongo_db_connection import MongoDBDAO
from document_retrieval.models.db_models import WorkflowStates

# Initialize MongoDB Data Access Object (DAO)
mongo_dao = MongoDBDAO()


def update_workflow_status(ecid: str, step: str) -> dict:
    """
    Updates the workflow status document in the MongoDB database.

    This function retrieves an existing workflow status document for the given ECID and step,
    updates its status to "completed," and records the update timestamp.

    Args:
        ecid (str): The External Case ID associated with the workflow.
        step (str): The specific step in the workflow to update.

    Returns:
        Dict[str, Any]: A dictionary containing the following keys:
            - success (bool): Indicates whether the operation was successful.
            - message (str): A message describing the outcome of the operation.
            - data (Any): The database update response or None if the operation failed.

    Example:
        >>> update_workflow_status("68809b22-3372-45f5-b0fb-b44346bb8efb", "trial-services")
        {
            "success": True,
            "message": "Successfully updated workflow status document for ECID: 68809b22-3372-45f5-b0fb-b44346bb8efb and step: trial-services",
            "data": <UpdateResult object>
        }
    """
    final_response = {
        "success": False,
        "message": None,
        "data": None
    }

    try:
        # Fetch the workflow status document
        status_document = mongo_dao.find_one(
            collection_name="workflow-states",
            query={"ecid": ecid, "step": step}
        )

        if status_document is None:
            final_response["message"] = (
                f"Workflow status document not found for ECID: {ecid} and step: {step}"
            )
            return final_response

        created_at = status_document["createdAt"]

        # Create an updated document instance
        document = WorkflowStates(
            ecid=ecid,
            step=step,
            status="completed",
            createdAt=created_at,
            updatedAt=datetime.now()
        ).dict()

        # Update the document in MongoDB
        db_response = mongo_dao.update(
            collection_name="workflow-states",
            update_values=document,
            query={"ecid": ecid, "step": step}
        )

        # Check if the document was successfully updated
        if db_response.matched_count > 0:
            final_response.update({
                "success": True,
                "message": (
                    f"Successfully updated workflow status document for ECID: {ecid} and step: {step}"
                ),
                "data": db_response
            })
        else:
            final_response["message"] = (
                f"Failed to update workflow status document for ECID: {ecid} and step: {step}"
            )

        return final_response

    except Exception as e:
        final_response["message"] = f"Exception occurred: {str(e)}"
        return final_response


# Example Usage:
# update_workflow_status("68809b22-3372-45f5-b0fb-b44346bb8efb", "trial-services")
