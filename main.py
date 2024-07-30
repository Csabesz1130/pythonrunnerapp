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

        credentials_path = r"C:\Users\Balogh Csaba\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-331f965683.json"

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        firestore_service = FirestoreService(credentials_path)

        if firestore_service is None:
            raise ValueError("FirestoreService initialization failed")

        main_window = MainWindow(firestore_service)
        main_window.show()

        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"An error occurred while starting the application: {e}", exc_info=True)
        QMessageBox.critical(None, "Startup Error", f"An error occurred while starting the application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()