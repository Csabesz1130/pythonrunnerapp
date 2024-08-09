from PyQt6.QtCore import QThread, pyqtSignal
import logging

class DataFetchThread(QThread):
    data_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)

    def __init__(self, firestore_service, collection, festival):
        super().__init__()
        self.firestore_service = firestore_service
        self.collection = collection
        self.festival = festival

    def run(self):
        try:
            logging.info(f"Starting data fetch for {self.collection}, festival: {self.festival}")
            companies = self.firestore_service.get_companies(self.collection, self.festival)

            total_items = len(companies)
            chunk_size = 20  # Adjust this value based on your needs
            for i in range(0, total_items, chunk_size):
                chunk = companies[i:i+chunk_size]
                self.data_fetched.emit(chunk)
                self.progress_updated.emit(i + len(chunk), total_items)
                self.msleep(10)  # Small delay to avoid overwhelming the UI

            logging.info(f"Data fetch completed for {self.collection}, festival: {self.festival}")
        except Exception as e:
            error_msg = f"Error fetching data: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)