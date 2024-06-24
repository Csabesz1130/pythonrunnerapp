import sys
import logging
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.main_window import MainWindow
from src.firestore_service import FirestoreService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        app = QApplication(sys.argv)

        # Initialize FirestoreService
        credentials_path = r"resources\runnerapp-232cc-firebase-adminsdk-2csiq-ab213e15ac.json"

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        firestore_service = FirestoreService(credentials_path)

        # Create MainWindow with FirestoreService
        main_window = MainWindow(firestore_service)
        main_window.show()

        sys.exit(app.exec())
    except FileNotFoundError as e:
        logging.error(f"Firebase credentials file not found: {e}")
        QMessageBox.critical(None, "Error", f"Firebase credentials file not found. Please check the file path: {credentials_path}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        QMessageBox.critical(None, "Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
   main()
