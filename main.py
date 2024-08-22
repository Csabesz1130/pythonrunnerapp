import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from firestore_service import FirestoreService

def exception_hook(exctype, value, traceback):
    logging.error("Uncaught exception", exc_info=(exctype, value, traceback))
    sys.exit(1)

def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filename='app_log.txt',
                        filemode='w')

    # Set the exception hook
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)

    try:
        # Get the path to the credentials file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'src', 'runnerapp-232cc-firebase-adminsdk-2csiq-331f965683.json')

        logging.info(f"Initializing FirestoreService with credentials: {credentials_path}")
        firestore_service = FirestoreService(credentials_path)

        logging.info("Creating MainWindow")
        main_window = MainWindow(firestore_service)

        logging.info("Showing MainWindow")
        main_window.show()

        # Use a timer to log if the event loop starts successfully
        QTimer.singleShot(0, lambda: logging.info("Event loop started"))

        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()