import os
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.main_window import MainWindow
from src.firestore_service import FirestoreService

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the path to your credentials file
CREDENTIALS_PATH = r"C:\Users\Balogh Csaba\advancedmodelrunnerapp\pythonrunnerapp\src\runnerapp-232cc-firebase-adminsdk-2csiq-331f965683.json"

# Set the environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

# Log the current value of the environment variable
logging.debug(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

def main():
    app = QApplication(sys.argv)

    try:
        # Initialize FirestoreService with the credentials path
        firestore_service = FirestoreService(CREDENTIALS_PATH)

        # Create and show the main window
        main_window = MainWindow(firestore_service)
        main_window.show()

        # Start the application event loop
        sys.exit(app.exec())
    except ValueError as e:
        logging.critical(f"Failed to initialize application: {e}")
        QMessageBox.critical(None, "Initialization Error", str(e))
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
        QMessageBox.critical(None, "Unexpected Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()