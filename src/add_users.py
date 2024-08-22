import logging
from firestore_service import FirestoreService
import sys
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def add_initial_users():
    try:
        # Get the path to the credentials file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'src', 'runnerapp-232cc-firebase-adminsdk-2csiq-331f965683.json')

        logging.info(f"Initializing FirestoreService with credentials: {credentials_path}")
        firestore_service = FirestoreService(credentials_path)
    except ValueError as e:
        logging.error(f"Failed to initialize FirestoreService: {e}")
        return

    users_to_add = [
        ("csaba", "1234576", "superuser"),
        ("hds", "1234567", "superuser")
    ]

    for username, password, role in users_to_add:
        logging.info(f"Attempting to add user: {username}")
        try:
            success, message = firestore_service.add_user(username, password, role)
            if success:
                logging.info(f"Added user: {username}")
            else:
                logging.error(f"Failed to add user {username}: {message}")
        except Exception as e:
            logging.error(f"Exception while adding user {username}: {e}", exc_info=True)

    # Verify users were added
    for username, _, _ in users_to_add:
        try:
            user = firestore_service.get_user(username)
            if user:
                logging.info(f"Verified user exists: {username}")
            else:
                logging.error(f"User not found after addition: {username}")
        except Exception as e:
            logging.error(f"Exception while verifying user {username}: {e}", exc_info=True)

    # List all users in the database
    logging.info("Listing all users in the database:")
    try:
        all_users = firestore_service.db.collection('users').get()
        for user in all_users:
            user_data = user.to_dict()
            logging.info(f"User: {user_data.get('username')}, Role: {user_data.get('role')}")
    except Exception as e:
        logging.error(f"Exception while listing users: {e}", exc_info=True)

if __name__ == "__main__":
    add_initial_users()
    input("Press Enter to exit...")  # This will keep the console window open