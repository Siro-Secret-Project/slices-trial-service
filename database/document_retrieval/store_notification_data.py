from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from document_retrieval.models.db_models import NotificationData
from typing import Dict, Any

# Initialize MongoDB Data Access Object (DAO)
mongo_dao = MongoDBDAO()

def store_notification_data(ecid: str) -> Dict[str, Any]:
    """
    Stores notification data in the MongoDB database.

    This function creates a document using the `NotificationData` model, inserts it into the
    'notifications' collection, and returns a response indicating success or failure.

    Args:
        ecid (str): The Job ID associated with the Job Run

    Returns:
        Dict[str, Any]: A dictionary containing the following keys:
            - success (bool): Indicates whether the operation was successful.
            - message (str): A message describing the outcome of the operation.
            - data (Any): The inserted document's ID or None if the operation failed.

    Example:
        >>> store_notification_data("john_doe", "ecid_123", "Your order has been shipped.")
        {
            "success": True,
            "message": "Successfully stored notification data: 65a1b2c3d4e5f6g7h8i9j0k",
            "data": <InsertOneResult object>
        }
    """
    # Initialize the response structure
    final_response = {
        "success": False,
        "message": "Failed to store notification data",
        "data": None
    }

    try:
        # Fetch User Name
        user_name_response =  mongo_dao.find_one(collection_name="similar_trials_results", query={"ecid": ecid}, projection={"userName": 1})
        user_name = user_name_response["userName"] if user_name_response else "Unknown User"

        # Notification Message

        notification_message = f"Hey {user_name}, your job with ECID: {ecid} has been completed successfully."
        # Create a document instance using the NotificationData model
        document = NotificationData(
            userName=user_name,
            ecid=ecid,
            notificationMessage=notification_message,
            createdAt=datetime.now(),  # Timestamp for record creation
            updatedAt=datetime.now()    # Timestamp for record update
        )

        # Insert the document into the MongoDB collection using DAO
        db_response = mongo_dao.insert("notifications", document.model_dump())

        # Check if the document was successfully inserted
        if db_response and db_response.inserted_id:
            final_response["success"] = True
            final_response["message"] = f"Successfully stored notification data: {db_response.inserted_id}"
            final_response["data"] = db_response
        else:
            final_response["message"] = "Failed to store notification data: No inserted ID returned."

        return final_response

    except Exception as e:
        # Log the exception and update the response with the error message
        final_response["message"] = f"Error storing notification data: {str(e)}"
        # Optionally, log the exception to a monitoring system (e.g., Sentry, Loggly)
        # logger.error(f"Error in store_notification_data: {str(e)}", exc_info=True)
        return final_response
