import sys
import logging
import os
from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.company_details_view_install import CompanyDetailsViewInstall
from src.company_details_view_demolition import CompanyDetailsViewDemolition
from src.edit_field_dialog import EditFieldDialog
from src.firestore_service import FirestoreService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        # Create QApplication instance first
        app = QApplication(sys.argv)

        # Initialize FirestoreService
        credentials_path = r"C:\Users\Balogh Csaba\IdeaProjects\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-a27b27e8c7.json"

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        firestore_service = FirestoreService(credentials_path)

        # Create MainWindow with FirestoreService
        main_window = MainWindow(firestore_service)
        main_window.show()

        # Start the event loop
        sys.exit(app.exec())
    except FileNotFoundError as e:
        logging.error(f"Firebase credentials file not found: {e}")
        print(f"Error: Firebase credentials file not found. Please check the file path: {credentials_path}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"Error: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()