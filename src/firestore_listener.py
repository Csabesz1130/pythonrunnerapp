from PyQt6.QtCore import QObject, pyqtSignal
import logging

class FirestoreListener(QObject):
    data_changed = pyqtSignal(dict, str)

    def __init__(self, firestore_service, collection):
        super().__init__()
        self.firestore_service = firestore_service
        self.collection = collection
        self.listener = None

    def start_listening(self):
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                try:
                    if change.type.name in ['ADDED', 'MODIFIED']:
                        data = change.document.to_dict()
                        data['Id'] = change.document.id  # Ensure ID is always present
                        self.data_changed.emit(data, change.type.name)
                    elif change.type.name == 'REMOVED':
                        self.data_changed.emit({'Id': change.document.id}, 'REMOVED')
                except Exception as e:
                    logging.error(f"Error processing Firestore change: {e}", exc_info=True)

        self.listener = self.firestore_service.db.collection(self.collection).on_snapshot(on_snapshot)
        logging.info(f"Started listening to collection: {self.collection}")

    def stop_listening(self):
        if self.listener:
            self.listener.unsubscribe()
            logging.info(f"Stopped listening to collection: {self.collection}")
        else:
            logging.warning("Attempted to stop listener that was not active")

    def __del__(self):
        self.stop_listening()