from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from document_retrieval.models.db_models import NotificationData
from typing import Dict, Any

# Initialize MongoDB Data Access Object (DAO)
mongo_dao = MongoDBDAO()

def store_notification_data(user_name: str, ecid: str, notification_message: str) -> Dict[str, Any]:
    """
    Stores notification data in the MongoDB database.

    This function creates a document using the `NotificationData` model, inserts it into the
    'notifications' collection, and returns a response indicating success or failure.

    Args:
        user_name (str): The username associated with the notification.
        ecid (str): The ECID (Enterprise Customer ID) associated with the notification.
        notification_message (str): The content of the notification message.

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
        # Create a document instance using the NotificationData model
        document = NotificationData(
            userName=user_name,
            ecid=ecid,
            notificationMessage=notification_message,
            created_at=datetime.now(),  # Timestamp for record creation
            updated_at=datetime.now()    # Timestamp for record update
        ).dict()

        # Insert the document into the MongoDB collection using DAO
        db_response = mongo_dao.insert("notifications", document)

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
